from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.core.database import db
from src.core.Inmueble.property import Property
from src.core.Usuario.User import User
from flask_login import login_required, current_user


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
@bp.route("/create", methods=["GET"])
@login_required
def create():
    if not current_user.tiene_permiso('properties_create'):
        flash("No tienes permisos para esta acción", "danger")
        return redirect(url_for('property.index'))
    
    return render_template("Propiedades/create.html")

# Formulario de edición
@bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
    property = Property.query.get_or_404(id)
    
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
        flash("Propiedad actualizada", "success")
        return redirect(url_for('property.show', id=id))
    
    return render_template("Propiedades/edit.html", property=property)