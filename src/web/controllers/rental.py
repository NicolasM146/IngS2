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
from src.core.Reserva.UpgradeRequest import UpgradeRequest

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

#####################################
from flask_mail import Message
from flask import url_for


def enviar_mail_upgrade(cliente, upgrade_request):
    from src.web import mail  # Importar aquí para evitar import circular
    from datetime import datetime

    aceptar_url = url_for('rental.upgrade_confirmar', request_id=upgrade_request.id, _external=True)
    rechazar_url = url_for('rental.upgrade_cancelar', request_id=upgrade_request.id, _external=True)

    hoy = datetime.utcnow().date()
    fecha_inicio = upgrade_request.old_reservation.start_date
    fecha_a_mostrar = fecha_inicio if fecha_inicio >= hoy else hoy

    msg = Message("Solicitud de Upgrade de Reserva",
                  sender="noreply@tualquiler.com",
                  recipients=[cliente.email])
    
    msg.body = f"""
Hola {cliente.nombre},

Por los inconvenientes con la reserva en {upgrade_request.old_reservation.property.direccion}.

Dirección nueva: {upgrade_request.new_rental.property.direccion}
Fechas: {fecha_a_mostrar.strftime('%d/%m/%Y')} - {upgrade_request.old_reservation.end_date.strftime('%d/%m/%Y')}

¿Deseás aceptar esta mejora?

✅ Aceptar: {aceptar_url}
❌ Rechazar: {rechazar_url}

Gracias por usar nuestro servicio.
"""
    mail.send(msg)
    
from sqlalchemy.orm.exc import StaleDataError

@bp.route('/upgrade/confirmar/<int:request_id>')
def upgrade_confirmar(request_id):
    try:
        req = UpgradeRequest.query.with_for_update().get_or_404(request_id)
        
        if req.accepted is not None:
            flash('Esta solicitud ya fue procesada.', 'warning')
            return redirect(url_for('rental.index'))

        # Crear reserva nueva, borrar reserva vieja y solicitud
        reserva = req.old_reservation
        nueva_reserva = Reservation(
            start_date=max(datetime.utcnow().date(), reserva.start_date),
            end_date=reserva.end_date,
            price_per_night=reserva.price_per_night,
            advance_payment=reserva.advance_payment,
            status='pending',
            rental=req.new_rental,
            user=reserva.user,
        )
        
        for c in reserva.compañeros:
            nueva_reserva.compañeros.append(c)

        db.session.add(nueva_reserva)
        db.session.delete(reserva)
        db.session.delete(req)
        db.session.commit()

        flash('Upgrade confirmado y reserva actualizada.', 'success')
    except StaleDataError:
        db.session.rollback()
        flash('La solicitud fue modificada por otro proceso', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error: {e}', 'danger')

    return redirect(url_for('rental.index'))


@bp.route('/upgrade/cancelar/<int:request_id>')
def upgrade_cancelar(request_id):
    req = UpgradeRequest.query.get_or_404(request_id)

    if req.accepted is not None:
        flash('Esta solicitud ya fue procesada.', 'warning')
        return redirect(url_for('rental.index'))

    # Primero borrar la solicitud para liberar la FK
    db.session.delete(req)

    # Luego borrar la reserva original
    db.session.delete(req.old_reservation)

    db.session.commit()

    flash('Upgrade rechazado. Se canceló la reserva original.', 'info')
    return redirect(url_for('rental.index'))


    
@bp.route('/reserva/<int:reservation_id>/upgrade', methods=['GET', 'POST'])
@permiso_required('reservations_update')
@login_required
def upgrade_reservation(reservation_id):
    reserva = Reservation.query.get_or_404(reservation_id)
    hoy = datetime.utcnow().date()
    nuevo_inicio = max(hoy, reserva.start_date)
    nuevo_fin = reserva.end_date

    alquileres_disponibles = (
        Rental.query
        .filter(Rental.is_active == True)
        .filter(~Rental.reservations.any(
            and_(
                Reservation.start_date <= nuevo_fin,
                Reservation.end_date >= nuevo_inicio
            )
        ))
        .all()
    )

    if request.method == 'POST':
        nuevo_rental_id = request.form.get('nuevo_rental_id')
        nuevo_rental = Rental.query.get(nuevo_rental_id)

        if not nuevo_rental:
            flash('Alquiler seleccionado inválido.', 'danger')
            return redirect(url_for('rental.upgrade_reservation', reservation_id=reservation_id))

        # Crear solicitud de upgrade
        solicitud = UpgradeRequest(
            old_reservation=reserva,
            new_rental=nuevo_rental
        )
        db.session.add(solicitud)
        db.session.commit()

        enviar_mail_upgrade(reserva.user, solicitud)

        flash('Se envió un correo al cliente para confirmar el upgrade.', 'info')
        return redirect(url_for('rental.index'))

    return render_template('Alquileres/upgrade_form.html',
                           reserva=reserva,
                           alquileres=alquileres_disponibles,
                           nuevo_inicio=nuevo_inicio,
                           nuevo_fin=nuevo_fin)

#######################################################################################

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