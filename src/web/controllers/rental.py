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
from src.core.Reserva.reservation import Reservation
from sqlalchemy import and_

bp = Blueprint('rental', __name__, url_prefix='/rentals')

#se agrego el filtrado en la ruta index

@bp.route('/', methods=['GET'])
@permiso_required('rentals_index')
@login_required
def index():
    direccion = request.args.get("direccion")
    localidad = request.args.get("localidad")
    estado = request.args.get("estado")

    alquileres = []

    if request.args:  # Si se presionó "Buscar" (aunque los campos estén vacíos)
        query = Rental.query.join(Property)

        if direccion:
            query = query.filter(Property.direccion.ilike(f"%{direccion}%"))

        if localidad:
            query = query.filter(Property.localidad.ilike(f"%{localidad}%"))

        if estado == "libre":
            query = query.filter(Rental.is_active == True)
        elif estado == "bloqueado":
            query = query.filter(Rental.is_active == False)

        alquileres = query.all()

        # Filtro por funciones de Python
        if estado == "reservado":
            alquileres = [a for a in alquileres if a.reserved_today_or_later()]
        elif estado == "no_reservado":
            alquileres = [a for a in alquileres if not a.reserved_today_or_later()]

    return render_template("Alquileres/index.html", alquileres=alquileres)

@bp.route('/<int:rental_id>/reservas/vigentes')
@permiso_required("rentals_update")
@login_required
def listado_de_reservas(rental_id):
    hoy = datetime.utcnow().date()
    reservas = Reservation.query.filter(
        Reservation.end_date > hoy,
        Reservation.rental_id == rental_id
    ).order_by(Reservation.start_date).all()
    return render_template("Alquileres/current_reservation.html", reservas=reservas)


@bp.route('/reserva/<int:reservation_id>/upgrade', methods=['GET', 'POST'])
@permiso_required('reservations_update')
@login_required
def upgrade_reservation(reservation_id):
    reserva = Reservation.query.get_or_404(reservation_id)
    hoy = datetime.utcnow().date()
    
    # calcular fechas para búsqueda
    nuevo_inicio = max(hoy, reserva.start_date)
    nuevo_fin = reserva.end_date

    # buscar alquileres disponibles en ese rango
    alquileres_disponibles = (
        Rental.query
        .filter(Rental.is_active == True)
        .filter(
            ~Rental.reservations.any(
                and_(
                    Reservation.start_date <= nuevo_fin,
                    Reservation.end_date >= nuevo_inicio
                )
            )
        )
        .all()
    )

    if request.method == 'POST':
        nuevo_rental_id = request.form.get('nuevo_rental_id')
        nuevo_rental = Rental.query.get(nuevo_rental_id)

        if not nuevo_rental:
            flash('Alquiler seleccionado inválido.', 'danger')
            return redirect(url_for('rental.upgrade_reservation', reservation_id=reservation_id))

        # Calcular fecha inicio según regla: si hoy > reserva.start_date uso hoy, sino reserva.start_date
        hoy = datetime.utcnow().date()
        nuevo_inicio = hoy if hoy > reserva.start_date else reserva.start_date
        nuevo_fin = reserva.end_date  # Siempre el mismo fin

        # Crear nueva reserva copiando datos excepto rental_id y fechas
        nueva_reserva = Reservation(
            start_date=nuevo_inicio,
            end_date=nuevo_fin,
            price_per_night=reserva.price_per_night,     # mantiene precio viejo
            advance_payment=reserva.advance_payment,     # mantiene modalidad de pago vieja
            status=reserva.status,
            rental=nuevo_rental,
            user=reserva.user,
        )

        # Copiar compañeros
        for c in reserva.compañeros:
            nueva_reserva.compañeros.append(c)

        db.session.add(nueva_reserva)
        db.session.delete(reserva)
        db.session.commit()

        flash('Reserva actualizada con el nuevo alquiler correctamente.', 'success')
        return redirect(url_for('rental.index'))

    return render_template('Alquileres/upgrade_form.html',
                           reserva=reserva,
                           alquileres=alquileres_disponibles,
                           nuevo_inicio=nuevo_inicio,
                           nuevo_fin=nuevo_fin)
    
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
        advance_payment = request.form.get('advance_payment') == 'true'

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
            is_active=True,
            advance_payment=advance_payment,
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
def edit(rental_id):
    alquiler = Rental.query.get_or_404(rental_id)
    
    # Anteriormente se verificaba si el usuario actual era el que estaba almacenado como encargado del Inmueble alquilado, no tenia sentido.
    
    if request.method == 'POST':
        price = request.form.get('price')
        advance_payment = request.form.get('advance_payment') == 'true'

        try:
            price_float = float(price)
            if price_float < 0:
                raise ValueError("Precio inválido")
        except:
            flash("El precio debe ser un número positivo válido.", "danger")
            return redirect(url_for('rental.edit', rental_id=rental_id))

        alquiler.price = price_float
        alquiler.advance_payment = advance_payment
        
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

@bp.route("/<int:rental_id>/lock", methods=["POST"])
@permiso_required('rentals_update')
@login_required
def lock(rental_id):
    alquiler = Rental.query.get_or_404(rental_id)
    if alquiler.property.user_id != current_user.id:
        flash("No tienes permiso para bloquear este alquiler.", "danger")
        return redirect(url_for('rental.show', rental_id=rental_id))
    alquiler.is_active = False
    db.session.commit()
    flash("Alquiler bloqueado correctamente.", "success")
    return redirect(url_for('rental.show', rental_id=rental_id))


@bp.route("/<int:rental_id>/unlock", methods=["POST"])
@permiso_required('rentals_update')
@login_required
def unlock(rental_id):
    alquiler = Rental.query.get_or_404(rental_id)
    if alquiler.property.user_id != current_user.id:
        flash("No tienes permiso para liberar este alquiler.", "danger")
        return redirect(url_for('rental.show', rental_id=rental_id))
    alquiler.is_active = True
    db.session.commit()
    flash("Alquiler liberado correctamente.", "success")
    return redirect(url_for('rental.show', rental_id=rental_id))