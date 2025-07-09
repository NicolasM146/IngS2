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
from datetime import date
from src.core.Inmueble.localidad.Localidad import Localidad


bp = Blueprint('rental', __name__, url_prefix='/rentals')


@bp.route('/', methods=['GET'])
@permiso_required('rentals_index')
@login_required
def index():
    direccion = request.args.get("direccion")
    localidad_id = request.args.get("localidad_id")
    estado = request.args.get("estado")

    alquileres = []

    # Localidades para el select
    localidades = Localidad.query.order_by(Localidad.nombre).all()

    if request.args:
        query = Rental.query.join(Property)

        if direccion:
            query = query.filter(Property.direccion.ilike(f"%{direccion}%"))

        if localidad_id:
            query = query.filter(Property.localidad_id == int(localidad_id))

        if estado == "libre":
            query = query.filter(Rental.is_active == True)
        elif estado == "bloqueado":
            query = query.filter(Rental.is_active == False)

        alquileres = query.all()

        if estado == "reservado":
            alquileres = [a for a in alquileres if a.reserved_today_or_later()]
        elif estado == "no_reservado":
            alquileres = [a for a in alquileres if not a.reserved_today_or_later()]

    return render_template(
        "Alquileres/index.html",
        alquileres=alquileres,
        localidades=localidades,
        request_args=request.args
    )

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


from flask_mail import Message
from flask import url_for
from datetime import datetime

def enviar_mail_upgrade(cliente, upgrade_request):
    from src.web import mail  # Evitar import circular

    aceptar_url = url_for('rental.upgrade_confirmar', request_id=upgrade_request.id, _external=True)
    rechazar_url = url_for('rental.upgrade_cancelar', request_id=upgrade_request.id, _external=True)

    hoy = datetime.utcnow().date()
    fecha_inicio = upgrade_request.old_reservation.start_date
    fecha_a_mostrar = fecha_inicio if fecha_inicio >= hoy else hoy

    msg = Message("Solicitud de Upgrade de Reserva",
                  sender="noreply@tualquiler.com",
                  recipients=[cliente.email])

    # Texto plano (por si el cliente no soporta HTML)
    msg.body = f"""
Hola {cliente.nombre},

Por los inconvenientes con la reserva en{upgrade_request.old_reservation.rental.property.localidad.nombre}, {upgrade_request.old_reservation.rental.property.direccion}.

Dirección nueva: {upgrade_request.new_rental.property.direccion}
Fechas: {fecha_a_mostrar.strftime('%d/%m/%Y')} - {upgrade_request.old_reservation.end_date.strftime('%d/%m/%Y')}

¿Deseás aceptar esta mejora?

✅ Aceptar: {aceptar_url}
❌ Rechazar: {rechazar_url}

Gracias por usar nuestro servicio.
"""

    # Versión HTML
    msg.html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Hola {cliente.nombre},</h2>
        <p>
            Te contactamos debido a un inconveniente con tu reserva en:<br>
            <strong>{upgrade_request.old_reservation.rental.property.localidad.nombre}, {upgrade_request.old_reservation.rental.property.direccion}</strong>

        </p>
        <p>
            Te proponemos una mejora en:<br>
            <strong>{upgrade_request.new_rental.property.localidad.nombre}, {upgrade_request.new_rental.property.direccion}</strong><br>
            <b>Fechas:</b> {fecha_a_mostrar.strftime('%d/%m/%Y')} - {upgrade_request.old_reservation.end_date.strftime('%d/%m/%Y')}
        </p>
        <p>¿Deseás aceptar esta mejora?</p>
        <p>
            <a href="{aceptar_url}" style="padding: 10px 15px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">✅ Aceptar</a>
            &nbsp;&nbsp;
            <a href="{rechazar_url}" style="padding: 10px 15px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px;">❌ Rechazar</a>
        </p>
        <br>
        <p>Gracias por usar nuestro servicio.</p>
    </body>
    </html>
    """

    mail.send(msg)

    
from sqlalchemy.orm.exc import StaleDataError
@bp.route('/upgrade/confirmar/<int:request_id>')
def upgrade_confirmar(request_id):
    try:
        req = UpgradeRequest.query.with_for_update().get(request_id)
        if not req:
            flash('Esta solicitud ya no está disponible.', 'warning')
            return redirect(url_for('rental.index'))
        # Si ya fue aceptada o rechazada
        if req.accepted is not None:
            flash('Esta solicitud ya fue procesada.', 'warning')
            return redirect(url_for('rental.index'))

        # Obtener la reserva vieja
        reserva = req.old_reservation

        # Crear nueva reserva con mismos datos, pero en el nuevo alquiler
        nueva_reserva = Reservation(
            start_date=max(datetime.utcnow().date(), reserva.start_date),
            end_date=reserva.end_date,
            price_per_night=reserva.price_per_night,
            advance_payment=reserva.advance_payment,
            status='pending',
            rental=req.new_rental,
            user=reserva.user,
        )

        # Copiar compañeros
        for c in reserva.compañeros:
            nueva_reserva.compañeros.append(c)

        # Agregar la nueva reserva
        db.session.add(nueva_reserva)

        # Borrar primero la solicitud (para liberar la FK)
        db.session.delete(req)
        db.session.flush()  # 💥 esto es esencial

        # Luego borrar la reserva antigua
        db.session.delete(reserva)

        # Confirmar todos los cambios
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
    try:
        req = UpgradeRequest.query.with_for_update().get(request_id)
        if not req:
            flash('Esta solicitud ya no está disponible.', 'warning')
            return redirect(url_for('rental.index'))
        if req.accepted is not None:
            flash('Esta solicitud ya fue procesada.', 'warning')
            return redirect(url_for('rental.index'))

        # Primero eliminar la solicitud (libera la FK)
        db.session.delete(req)
        db.session.flush()  # 🔒 Fuerza el delete en la base antes de continuar

        # Luego eliminar la reserva original
        db.session.delete(req.old_reservation)

        db.session.commit()
        flash('Upgrade rechazado. Se canceló la reserva original.', 'info')

    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error: {e}', 'danger')

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
    # Subconsulta: propiedades con al menos un alquiler activo
    subquery = (
        db.session.query(Rental.property_id)
        .filter(or_(
            Rental.is_active == True,
            Rental.description == "locked"
        ))
        .subquery()
    )

    # Queremos propiedades que NO están en la subconsulta de activos
    propiedades = (
        db.session.query(Property)
        .filter(~Property.id.in_(subquery))  # "~" = NOT
        .all()
    )

    if request.method == 'POST':
        property_id = request.form.get('property_id')
        price = request.form.get('price')
        advance_payment = request.form.get('advance_payment') == 'true'

        propiedad = Property.query.filter_by(id=property_id).first()
        if not propiedad:
            flash("No se encuentra en el sistema, la propiedad seleccionada.", "danger")
            return redirect(url_for('rental.create'))

        alquiler_existente = Rental.query.filter_by(property_id=property_id, is_active=True).first()
        if alquiler_existente:
            flash("Ya existe un alquiler activo asociado a esta propiedad.", "warning")
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
            description="",
            is_active=True,
            advance_payment=advance_payment,
        )
        propiedad.estado = "publicado"
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
@login_required
def show(rental_id):
    alquiler = Rental.query.get_or_404(rental_id)
     # Lógica para permitir reseñar si hay reservas ya iniciadas
    puede_dejar_resena = Reservation.query.filter_by(
        user_id=current_user.id,
        rental_id=alquiler.id
    ).filter(Reservation.start_date <= date.today()).count() > 0

    review_summary = alquiler.get_review_summary()
    average_rating = alquiler.get_average_rating()
    reviews = sorted(alquiler.reviews, key=lambda r: r.created_at, reverse=True)

    return render_template(
        "Alquileres/show.html",
        alquiler=alquiler,
        review_summary=review_summary,
        average_rating=average_rating,
        reviews=reviews,
        puede_dejar_resena=puede_dejar_resena
    )

@bp.route("/<int:rental_id>/lock", methods=["POST"])
@permiso_required('rentals_update')
@login_required
def lock(rental_id):
    alquiler = Rental.query.get_or_404(rental_id)
    # Solo el encargado (check In/Out) puede bloquear o liberar el alquiler.
    if alquiler.property.user_id != current_user.id:
        flash("No tienes permiso para bloquear este alquiler.", "danger")
        return redirect(url_for('rental.show', rental_id=rental_id))
    alquiler.is_active = False
    alquiler.description = "locked"
    alquiler.property.estado = "bloqueado"
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
    alquiler.description = ""
    alquiler.property.estado = "publicado"
    db.session.commit()
    flash("Alquiler liberado correctamente.", "success")
    return redirect(url_for('rental.show', rental_id=rental_id))

@bp.route("/<int:rental_id>/unpublish", methods=["POST"])
@permiso_required('rentals_update')
@login_required
def unpublish(rental_id):
    rental = Rental.query.get_or_404(rental_id)

    rental.property.estado = "disponible"
    rental.is_active = False
    rental.description = ""
    db.session.commit()

    flash("Publicación eliminada correctamente.", "success")
    return redirect(url_for("rental.index"))
