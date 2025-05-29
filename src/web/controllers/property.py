from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.core.database import db
from src.core.Inmueble.property import Property
from src.core.Usuario.User import User
from flask_login import login_required, current_user
from src.web.forms.forms import PropertyForm


bp = Blueprint("property", __name__, url_prefix="/property")

@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        # Obtener todas las propiedades desde la base de datos
        properties = Property.query.all()  # Usando SQLAlchemy como ejemplo
        
        # Verificar si no hay resultados
        no_results = len(properties) == 0
        
        # Renderizar la plantilla con los datos
        return render_template(
            "Propiedades/index.html",
            properties=properties,
            no_results=no_results
        )
    
    elif request.method == "POST":
        # Parte POST (pendiente de implementación)
        pass
    
# Detalle de propiedad
@bp.route("/<int:id>")
@login_required
def show(id):
    property = Property.query.get_or_404(id)
    return render_template("Propiedades/show.html", property=property)

# Formulario de creación
@bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if not current_user.tiene_permiso('properties_create'):
        flash("No tienes permisos para crear propiedades", "danger")
        return redirect(url_for('property.index'))

    form = PropertyForm()  # Crea la instancia del formulario

    if form.validate_on_submit():
        # Lógica para guardar la propiedad
        
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
        flash('Carga del Inmueble exitosa')
        return redirect(url_for('property.index'))

    return render_template("Propiedades/create.html", form=form)

# Formulario de edición
@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    property = Property.query.get_or_404(id)
    users = User.query.all()  # O filtrar según tus necesidades
    
    if not current_user.tiene_permiso('properties_update'):
        flash("No tienes permisos para editar", "danger")
        return redirect(url_for('property.index'))
    
    if request.method == "POST":
        property.direccion = request.form.get('direccion')
        property.localidad = request.form.get('localidad')
        property.descripcion = request.form.get('descripcion')
        property.capacidad = request.form.get('capacidad')
        property.habitaciones = request.form.get('habitaciones')
        db.session.commit()
        flash("Actualización de Inmueble exitosa")
        return redirect(url_for('property.show', id=id))
    
    return render_template("Propiedades/edit.html", property=property, users=users)

@bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    if not current_user.tiene_permiso('properties_destroy'):
        flash("No tienes permisos para eliminar propiedades", "danger")
        return redirect(url_for('property.index'))
    
    property = Property.query.get_or_404(id)
    db.session.delete(property)
    db.session.commit()
    flash("Inmueble eliminado correctamente")
    return redirect(url_for('property.index'))