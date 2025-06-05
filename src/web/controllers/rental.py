from flask import Blueprint, render_template
from flask_login import login_required, current_user
from src.core.database import db
from src.core.Alquiler.Rental import Rental
from src.core.Inmueble.property import Property
from flask import request, redirect, url_for, flash
from datetime import datetime
from sqlalchemy.orm import aliased
from sqlalchemy import or_
from flask_login import login_required, current_user
from src.web.handlers.auth import permiso_required


bp = Blueprint('rental', __name__, url_prefix='/rentals')

#se agrego el filtrado en la ruta index

@bp.route('/', methods=['GET'])
@permiso_required('rentals_index')
@login_required
def index():
    query = Rental.query.join(Property)

    direccion = request.args.get("direccion")
    localidad = request.args.get("localidad")
    estado = request.args.get("estado")

    if direccion:
        query = query.filter(Property.direccion.ilike(f"%{direccion}%"))

    if localidad:
        query = query.filter(Property.localidad.ilike(f"%{localidad}%"))

    if estado == "libre":
        query = query.filter(Rental.is_active == True)
    elif estado == "bloqueado":
        query = query.filter(Rental.is_active == False)

    alquileres = query.all()

    return render_template("Alquileres/index.html", alquileres=alquileres)

@bp.route('/create', methods=['GET', 'POST'])
@permiso_required('rentals_create')
@login_required
def create():
    # Alias para Rental
    rental_alias = aliased(Rental)

    # Propiedades del usuario sin alquiler activo
    propiedades = (
        db.session.query(Property)
        .outerjoin(rental_alias, Property.id == rental_alias.property_id)
        .filter(
            Property.user_id == current_user.id,
            or_(rental_alias.id == None, rental_alias.is_active == False)
        )
        .all()
    )

    if request.method == 'POST':
        property_id = request.form.get('property_id')
        price = request.form.get('price')
        description = request.form.get('description')

        # Validar propiedad seleccionada
        propiedad = Property.query.filter_by(id=property_id, user_id=current_user.id).first()
        if not propiedad:
            flash("La propiedad seleccionada no es válida o no te pertenece.", "danger")
            return redirect(url_for('rental.create'))

        # Validar que no exista ya un alquiler para esa propiedad (property_id es unique)
        alquiler_existente = Rental.query.filter_by(property_id=property_id).first()
        if alquiler_existente:
            flash("Ya existe un alquiler asociado a esta propiedad.", "warning")
            return redirect(url_for('rental.create'))

        try:
            price_float = float(price)
            if price_float < 0:
                raise ValueError("Precio inválido")
        except:
            flash("El precio debe ser un número positivo válido.", "danger")
            return redirect(url_for('rental.create'))

        nuevo_alquiler = Rental(
            property_id=property_id,
            creation_date=datetime.utcnow(),
            price=price_float,
            description=description,
            is_active=True
        )
        db.session.add(nuevo_alquiler)
        db.session.commit()
        flash("Carga de Alquiler exitosa", "success")
        return redirect(url_for('rental.index'))

    return render_template("Alquileres/create.html", propiedades=propiedades)

@bp.route("/<int:rental_id>/delete", methods=["POST"])
@permiso_required('rentals_destroy')
@login_required
def delete(rental_id):  # Cambia el parámetro para que coincida con la ruta
    alquiler = Rental.query.get_or_404(rental_id)

    # Solo permitir borrar si el alquiler pertenece al usuario actual
    if alquiler.property.user_id != current_user.id:
        flash("No tienes permiso para borrar este alquiler.", "danger")
        return redirect(url_for('rental.index'))

    reservas_activas = alquiler.reservations.count()  # como es lazy='dynamic', count() consulta la DB
    if reservas_activas > 0:
        flash("No se puede eliminar el alquiler porque tiene reservas asociadas.", "danger")
        return redirect(url_for('rental.index'))
    
    # Eliminar el alquiler
    db.session.delete(alquiler)
    db.session.commit()
    flash("Alquiler eliminado correctamente.", "success")
    return redirect(url_for('rental.index'))

# Agrega esta nueva ruta al final del archivo rental.py
@bp.route("/<int:rental_id>/edit", methods=["GET", "POST"])
@permiso_required('rentals_update')
@login_required
def edit(rental_id):  # Cambia el parámetro para que coincida con la ruta
    alquiler = Rental.query.get_or_404(rental_id)
    
    # Verificar que el alquiler pertenece al usuario actual
    if alquiler.property.user_id != current_user.id:
        flash("No tienes permiso para editar este alquiler.", "danger")
        return redirect(url_for('rental.index'))

    if request.method == 'POST':
        price = request.form.get('price')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'on'

        try:
            price_float = float(price)
            if price_float < 0:
                raise ValueError("Precio inválido")
        except:
            flash("El precio debe ser un número positivo válido.", "danger")
            return redirect(url_for('rental.edit', rental_id=rental_id))

        alquiler.price = price_float
        alquiler.description = description
        alquiler.is_active = is_active
        
        db.session.commit()
        flash("Alquiler actualizado con éxito", "success")
        return redirect(url_for('rental.show', rental_id=rental_id))

    return render_template("Alquileres/edit.html", alquiler=alquiler)

@bp.route("/<int:rental_id>")
@permiso_required('rentals_show')
@login_required
def show(rental_id):
    alquiler = Rental.query.get_or_404(rental_id)
    if alquiler.property.user_id != current_user.id:
        flash("No tienes permiso para ver este alquiler.", "danger")
        return redirect(url_for('rental.index'))

    return render_template("Alquileres/show.html", alquiler=alquiler)