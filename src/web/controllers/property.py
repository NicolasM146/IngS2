from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.core.database import db
from src.core.Inmueble.property import Property
from src.core.Usuario.User import User
from flask_login import login_required, current_user
from src.web.forms.forms import PropertyForm, PropertySearchForm
from src.web.handlers.auth import permiso_required
import os
from werkzeug.utils import secure_filename
from src.core.Inmueble.property_photo import PropertyPhoto
from src.core.Inmueble.localidad.Localidad import Localidad
from src.core.Alquiler.Rental import Rental

bp = Blueprint("property", __name__, url_prefix="/property")

@bp.route("/", methods=["GET", "POST"])
@permiso_required('properties_index')
@login_required
def index():
    form = PropertySearchForm()
    properties = []
    no_results = False
    busqueda_realizada = False

    if form.validate_on_submit():
        query = Property.query
        if form.direccion.data:
            query = query.filter(Property.direccion.ilike(f'%{form.direccion.data}%'))
        if form.localidad.data:
            query = query.filter(Property.localidad_id == form.localidad.data.id)
        if form.estado.data:
            query = query.filter(Property.estado == form.estado.data)
        if form.capacidad.data:
            query = query.filter(Property.capacidad == int(form.capacidad.data))
        if form.habitaciones.data:
            query = query.filter(Property.habitaciones == int(form.habitaciones.data))
        subquery = (
            db.session.query(Rental.property_id)
            .filter(Rental.is_active == True)
            .subquery()
        )

        if form.publicado.data == 'si':
            query = query.filter(Property.id.in_(subquery))
        elif form.publicado.data == 'no':
            query = query.filter(~Property.id.in_(subquery))

        
        properties = query.all()
        no_results = len(properties) == 0
        busqueda_realizada = True

    return render_template(
        "Propiedades/index.html",
        properties=properties,
        no_results=no_results,
        busqueda_realizada=busqueda_realizada,
        form=form
    )

    
@bp.route("/<int:id>")
@permiso_required('properties_show')
@login_required
def show(id):
    property_obj = Property.query.get_or_404(id) # Renombrado para claridad
    return render_template("Propiedades/show.html", property=property_obj) # Pasar como 'property' al template

@bp.route("/create", methods=["GET", "POST"])
@permiso_required('properties_create')
@login_required
def create():
    form = PropertyForm()
    
    # Cargar localidades al formulario
    localidades = Localidad.query.order_by(Localidad.nombre).all()
    form.localidad.choices = [(loc.id, loc.nombre) for loc in localidades]

    if form.validate_on_submit():
        if 'photos' not in request.files:
            flash('No se encontró el campo de fotos en el formulario', 'danger')
            return redirect(request.url)
            
        files = request.files.getlist('photos')
        valid_files_for_upload = []
        for file in files:
            if file and file.filename:
                if not PropertyPhoto.allowed_file(file.filename):
                    flash(f'El archivo {file.filename} no tiene una extensión permitida (jpg, png, jpeg, gif)', 'danger')
                    return redirect(request.url)
                valid_files_for_upload.append(file)

        if not valid_files_for_upload:
            flash('Debe seleccionar al menos una foto válida.', 'danger')
            return redirect(request.url)
        
        if len(valid_files_for_upload) > 10:
            flash('Máximo 10 fotos permitidas', 'danger')
            return redirect(request.url)

        direccion = form.direccion.data.strip()
        localidad_obj = form.localidad.data    # Esto es un objeto Localidad completo
        localidad_id = localidad_obj.id

        # Validar si ya existe una propiedad con misma dirección y localidad
        propiedad_existente = Property.query.filter_by(direccion=direccion, localidad_id=localidad_id).first()
        if propiedad_existente:
            flash('Ya existe una propiedad registrada con esa dirección y localidad.', 'error')
            return render_template("Propiedades/create.html", form=form)

        new_property = Property(
            direccion=direccion,
            localidad_id=localidad_id,
            capacidad=form.capacidad.data,
            habitaciones=form.habitaciones.data,
            estado=form.estado.data,
            descripcion=form.descripcion.data,
            user_id=form.usuario_id.data
        )
        db.session.add(new_property)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la propiedad: ' + str(e), 'danger')
            return redirect(request.url)

        upload_folder = PropertyPhoto.get_upload_folder()
        os.makedirs(upload_folder, exist_ok=True)

        processed_photos_db_objects = []
        primary_photo_set = False

        for idx, file_to_save in enumerate(valid_files_for_upload):
            try:
                filename = secure_filename(f"{new_property.id}_{idx}_{file_to_save.filename}")
                filepath = os.path.join(upload_folder, filename)
                file_to_save.save(filepath)

                current_photo_is_primary = not primary_photo_set
                if not primary_photo_set:
                    primary_photo_set = True

                new_photo = PropertyPhoto(
                    filename=filename,
                    is_primary=current_photo_is_primary,
                    property_id=new_property.id
                )
                db.session.add(new_photo)
                processed_photos_db_objects.append(new_photo)
            except Exception as e:
                flash(f'Error al guardar la foto {file_to_save.filename}: {str(e)}', 'warning')
                continue

        if not processed_photos_db_objects:
            flash('No se pudo guardar ninguna foto. La propiedad no fue creada completamente.', 'danger')
            db.session.delete(new_property)
            db.session.commit()
            return redirect(request.url)

        try:
            db.session.commit()
            flash(f'Carga del Inmueble exitosa', 'success')
            return redirect(url_for('property.show', id=new_property.id))
        except Exception as e:
            db.session.rollback()
            flash('Error al guardar las fotos en la base de datos: ' + str(e), 'danger')
            return redirect(request.url)

    return render_template("Propiedades/create.html", form=form)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@permiso_required('properties_update')
@login_required
def edit(id):
    property_obj = Property.query.get_or_404(id)
    users = User.query.all()
    
    if not current_user.tiene_permiso('properties_update'):
        flash("No tienes permisos para actualizar propiedades.", "danger")
        return redirect(url_for('property.index'))
    
    if request.method == "POST":
        property_obj.direccion = request.form.get('direccion')
        property_obj.localidad_id = int(request.form.get('localidad'))
        property_obj.descripcion = request.form.get('descripcion')
        property_obj.capacidad = request.form.get('capacidad')
        property_obj.habitaciones = request.form.get('habitaciones')
        property_obj.estado = request.form.get('estado')
        property_obj.user_id = request.form.get('user_id')

        photo_ids_to_delete_str = request.form.getlist('delete_photos')
        new_photo_files_from_form = request.files.getlist('new_photos')
        
        valid_new_photo_files_to_upload = []
        invalid_file_extension_found = False
        for file_storage in new_photo_files_from_form:
            if file_storage and file_storage.filename:
                if not PropertyPhoto.allowed_file(file_storage.filename):
                    flash(f'El archivo tiene una extensión no permitida. Se guardaron los cambios pero las nuevas fotos no se procesarán.', 'warning')
                    invalid_file_extension_found = True
                    break
                valid_new_photo_files_to_upload.append(file_storage)
        
        if invalid_file_extension_found:
            valid_new_photo_files_to_upload = []

        num_photos_after_proposed_deletion = 0
        for p_photo_obj in property_obj.photos:
            if str(p_photo_obj.id) not in photo_ids_to_delete_str:
                num_photos_after_proposed_deletion += 1
        
        projected_final_photo_count = num_photos_after_proposed_deletion + len(valid_new_photo_files_to_upload)

        if projected_final_photo_count < 1:
            flash('Error: La propiedad debe tener al menos una foto. Revise las fotos a eliminar o agregue nuevas fotos válidas.', 'danger')
            return redirect(url_for('property.edit', id=id))

        if projected_final_photo_count > 10:
            flash(f'Error: No puede tener más de 10 fotos.', 'danger')
            return redirect(url_for('property.edit', id=id))

        photos_deleted_from_session = []
        if photo_ids_to_delete_str:
            for photo_id_str_to_delete in photo_ids_to_delete_str:
                photo_to_delete = PropertyPhoto.query.get(photo_id_str_to_delete)
                if photo_to_delete and photo_to_delete.property_id == property_obj.id:
                    file_path = os.path.join(PropertyPhoto.get_upload_folder(), photo_to_delete.filename)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except OSError as e:
                            flash(f'Advertencia: Error al eliminar el archivo físico {photo_to_delete.filename}: {e}', 'warning')
                    db.session.delete(photo_to_delete)
                    photos_deleted_from_session.append(photo_to_delete)

        if photos_deleted_from_session:
            db.session.flush()

        newly_added_photo_db_objects = []
        if valid_new_photo_files_to_upload:
            upload_folder = PropertyPhoto.get_upload_folder()
            os.makedirs(upload_folder, exist_ok=True)
            
            current_photo_count_for_naming = len(property_obj.photos) 

            for idx, photo_file_to_save in enumerate(valid_new_photo_files_to_upload):
                try:
                    filename_base = f"{property_obj.id}_{current_photo_count_for_naming + idx}"
                    filename = secure_filename(f"{filename_base}_{photo_file_to_save.filename}")
                    filepath = os.path.join(upload_folder, filename)
                    photo_file_to_save.save(filepath)
                    
                    new_photo_db_obj = PropertyPhoto(
                        filename=filename,
                        is_primary=False,
                        property_id=property_obj.id
                    )
                    db.session.add(new_photo_db_obj)
                    newly_added_photo_db_objects.append(new_photo_db_obj)
                except Exception as e:
                    flash(f'Advertencia: Error al guardar la nueva foto {photo_file_to_save.filename}: {str(e)}', 'warning')

        if newly_added_photo_db_objects:
            db.session.flush()
            
        selected_primary_photo_id_str = request.form.get('primary_photo')
        all_current_photos_for_property = PropertyPhoto.query.filter_by(property_id=property_obj.id).order_by(PropertyPhoto.id).all()

        if selected_primary_photo_id_str:
            for p_photo in all_current_photos_for_property:
                p_photo.is_primary = (str(p_photo.id) == selected_primary_photo_id_str)
        
        if all_current_photos_for_property:
            current_primary_photos = [p for p in all_current_photos_for_property if p.is_primary]

            if not current_primary_photos:
                all_current_photos_for_property[0].is_primary = True
            elif len(current_primary_photos) > 1:
                first_primary_found = False
                for p_photo in all_current_photos_for_property:
                    if p_photo.is_primary:
                        if not first_primary_found:
                            first_primary_found = True
                        else:
                            p_photo.is_primary = False
        try:
            db.session.commit()
            flash("Actualización de Inmueble exitosa.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error crítico al guardar los cambios en la base de datos: {str(e)}. Revise los datos e intente de nuevo.", "danger")
        
        return redirect(url_for('property.show', id=id))
    
    localidades = Localidad.query.order_by(Localidad.nombre).all()
    tiene_reservas_pendientes = False #Esto definira si se puede modificar o no la Localidad
    if property_obj.rental and property_obj.rental.reserved_today_or_later():
        tiene_reservas_pendientes = True
    return render_template("Propiedades/edit.html", property=property_obj, users=users, localidades=localidades, localidad_bloqueada=tiene_reservas_pendientes)


@bp.route("/delete/<int:id>", methods=["POST"])
@permiso_required('properties_destroy')
@login_required
def delete(id):
    property_obj = Property.query.get_or_404(id)

    # Verificar si tiene reservas activas
    if property_obj.rental and property_obj.rental.reservations.count() > 0:
        flash("Error, se tiene actividad registrada del Inmueble. No se pudo borrar el Inmueble", "danger")
        return redirect(url_for('property.index'))

    # Eliminar fotos asociadas del sistema de archivos
    upload_folder = PropertyPhoto.get_upload_folder()
    for photo in property_obj.photos:
        file_path = os.path.join(upload_folder, photo.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                flash(f"Advertencia: No se pudo eliminar el archivo {photo.filename}: {e}", "warning")

    # Eliminar inmueble
    db.session.delete(property_obj)
    db.session.commit()
    flash("Inmueble eliminado correctamente", "success")
    return redirect(url_for('property.index'))


@bp.route("/<int:id>/deactivate", methods=["POST"])
@permiso_required('properties_update')
@login_required
def deactivate(id):
    property_obj = Property.query.get_or_404(id) # Renombrado

    if not current_user.tiene_permiso('properties_update'):
        flash("No tienes permisos para dar de baja propiedades", "danger")
        return redirect(url_for('property.show', id=id))
    

    property_obj.estado = 'baja'
    db.session.commit()


    flash("Baja del inmueble exitosa", "success")
    return redirect(url_for('property.show', id=id))

@bp.route("/<int:id>/reactivate", methods=["POST"])
@permiso_required('properties_update')
@login_required
def reactivate(id):
    property_obj = Property.query.get_or_404(id) # Renombrado
    
    if not current_user.tiene_permiso('properties_update'):
        flash("No tienes permisos para reactivar propiedades", "danger")
        return redirect(url_for('property.show', id=id))
    
    property_obj.estado = 'disponible'
    db.session.commit()
    flash("Inmueble reactivado correctamente", "success")
    return redirect(url_for('property.show', id=id))

@bp.route("/localidad/agregar", methods=["GET", "POST"])
@permiso_required('properties_update')
@login_required
def agregar_localidad():
    if request.method == "POST":
        nombre = request.form.get("nombre").strip()

        if not nombre:
            flash("Debe ingresar un nombre para la localidad.", "warning")
        else:
            existente = Localidad.query.filter_by(nombre=nombre).first()
            if existente:
                flash("La localidad ya existe.", "warning")
            else:
                nueva = Localidad(nombre=nombre)
                db.session.add(nueva)
                db.session.commit()
                flash("Localidad agregada correctamente.", "success")
                return redirect(url_for("property.index"))

    return render_template("Propiedades/localidad_agregar.html")

@bp.route("/localidad/eliminar", methods=["GET", "POST"])
@permiso_required('properties_update')
@login_required
def eliminar_localidad():
    localidades_no_usadas = Localidad.query.outerjoin(Property).filter(Property.id == None).order_by(Localidad.nombre).all()

    if request.method == "POST":
        localidad_id = request.form.get("localidad_id")
        localidad = Localidad.query.get(localidad_id)

        if localidad:
            db.session.delete(localidad)
            db.session.commit()
            flash("Localidad eliminada correctamente.", "success")
            return redirect(url_for("property.index"))

    return render_template("Propiedades/localidad_eliminar.html", localidades=localidades_no_usadas)