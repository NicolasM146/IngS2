from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.core.database import db
from src.core.Inmueble.property import Property
from src.core.Usuario.User import User
from flask_login import login_required, current_user
from src.web.forms.forms import PropertyForm, PropertySearchForm
from src.web.handlers.auth import permiso_required


bp = Blueprint("property", __name__, url_prefix="/property")

@bp.route("/", methods=["GET", "POST"])
@permiso_required('properties_index')
@login_required
def index():
    form = PropertySearchForm()
    query = Property.query
    
    if form.validate_on_submit():
        # Filtro por dirección (búsqueda parcial)
        if form.direccion.data:
            query = query.filter(Property.direccion.ilike(f'%{form.direccion.data}%'))
        
        # Filtro por localidad (búsqueda exacta)
        if form.localidad.data:
            query = query.filter(Property.localidad.ilike(f'%{form.localidad.data}%'))
        
        # Filtro por estado
        if form.estado.data:
            query = query.filter(Property.estado == form.estado.data)
        
        # Filtros numéricos (mínimos)
        if form.capacidad.data:
            query = query.filter(Property.capacidad == int(form.capacidad.data))
        
        if form.habitaciones.data:
            query = query.filter(Property.habitaciones == int(form.habitaciones.data))
    
    properties = query.all()
    no_results = len(properties) == 0
    
    return render_template(
        "Propiedades/index.html",
        properties=properties,
        no_results=no_results,
        form=form
    )
    
# Vista del Inmueble
@bp.route("/<int:id>")
@permiso_required('properties_show')
@login_required
def show(id):
    property = Property.query.get_or_404(id)
    return render_template("Propiedades/show.html", property=property)

# Formulario de creación
@bp.route("/create", methods=["GET", "POST"])
@permiso_required('properties_create')
@login_required
def create():

    form = PropertyForm()  # Crea la instancia del formulario

    if form.validate_on_submit():
        # Lógica para guardar la propiedad
        direccion = form.direccion.data.strip()
        localidad = form.localidad.data.strip()

        # Validamos si ya existe una propiedad con esa dirección y localidad
        propiedad_existente = Property.query.filter_by(direccion=direccion, localidad=localidad).first()

        if propiedad_existente:
            flash('Ya existe una propiedad registrada con esa dirección y localidad.', 'error')
            return render_template("Propiedades/create.html", form=form)
        
        new_property = Property(
            direccion=form.direccion.data,
            localidad=form.localidad.data,
            capacidad=form.capacidad.data,
            habitaciones=form.habitaciones.data,
            estado=form.estado.data,
            descripcion=form.descripcion.data,
            user_id=current_user.id
        )
        db.session.add(new_property)
        db.session.commit()
        flash('Carga del Inmueble exitosa',"success")
        return redirect(url_for('property.index'))

    return render_template("Propiedades/create.html", form=form)

# Formulario de edición
@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@permiso_required('properties_edit')
@login_required
def edit(id):
    property = Property.query.get_or_404(id)
    users = User.query.all()  # O filtrar según tus necesidades
    
    
    if request.method == "POST":
        property.direccion = request.form.get('direccion')
        property.localidad = request.form.get('localidad')
        property.descripcion = request.form.get('descripcion')
        property.capacidad = request.form.get('capacidad')
        property.habitaciones = request.form.get('habitaciones')
        property.estado = request.form.get('estado')
        db.session.commit()
        flash("Actualización de Inmueble exitosa","success")
        return redirect(url_for('property.show', id=id))
    
    return render_template("Propiedades/edit.html", property=property, users=users)

@bp.route("/delete/<int:id>", methods=["POST"])
@permiso_required('properties_destroy')
@login_required
def delete(id):
    
    property = Property.query.get_or_404(id)
    db.session.delete(property)
    db.session.commit()
    flash("Inmueble eliminado correctamente","success")
    return redirect(url_for('property.index'))

@bp.route("/<int:id>/deactivate", methods=["POST"])
@permiso_required('properties_update')
@login_required
def deactivate(id):
    property = Property.query.get_or_404(id)

    if not current_user.tiene_permiso('properties_update'):
        flash("No tienes permisos para dar de baja propiedades", "danger")
        return redirect(url_for('property.show', id=id))

    property.estado = 'baja'
    db.session.commit()

    flash("Baja del inmueble exitosa", "success")
    return redirect(url_for('property.show', id=id))

@bp.route("/<int:id>/reactivate", methods=["POST"])
@permiso_required('properties_update')
@login_required
def reactivate(id):
    property = Property.query.get_or_404(id)
    
    if not current_user.tiene_permiso('properties_update'):
        flash("No tienes permisos para reactivar propiedades", "danger")
        return redirect(url_for('property.show', id=id))
    
    property.estado = 'disponible'
    db.session.commit()
    flash("Inmueble reactivado correctamente", "success")
    return redirect(url_for('property.show', id=id))