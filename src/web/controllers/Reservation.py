
from src.core.Alquiler.Rental import Rental
from src.core.Reserva.reservation import Reservation
from src.core.Usuario.Compañero import Compañero
from flask_login import login_required, current_user
from src.core.database import db
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for

import os
from dotenv import load_dotenv
import stripe

# Carga las variables de entorno del archivo .env
load_dotenv()

# Obtiene la clave secreta de Stripe desde la variable de entorno
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


bp = Blueprint('reservation', __name__, url_prefix='/reservacion')

@bp.route("/buscar_alquileres")
def buscar_alquileres():
    precio_min = request.args.get("precio_min", type=float)
    precio_max = request.args.get("precio_max", type=float)
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    localidad = request.args.get("localidad", type=str)
    habitaciones = request.args.get("habitaciones", type=int)
    cant_personas = request.args.get("cant_personas", type=int)

    query = Rental.query.filter_by(is_active=True)

    # Filtro precio
    if precio_min is not None:
        query = query.filter(Rental.price >= precio_min)

    if precio_max is not None:
        query = query.filter(Rental.price <= precio_max)

    # Filtro fechas: excluir alquileres reservados en ese rango
    if fecha_inicio and fecha_fin:
        try:
            fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

            # Subconsulta: reservas que se solapan con las fechas dadas
            subquery = db.session.query(Reservation.rental_id).filter(
                Reservation.start_date <= ff,
                Reservation.end_date >= fi
            ).subquery()

            # Filtrar alquileres que NO están en esas reservas (disponibles)
            query = query.filter(~Rental.id.in_(subquery))
        except ValueError:
            pass

    # Filtro localidad
    if localidad:
        query = query.filter(Rental.property.localidad.ilike(f"%{localidad}%"))

    # Filtro habitaciones
    if habitaciones:
        query = query.filter(Rental.property.habitaciones == habitaciones)

    # Filtro cantidad de personas
    if cant_personas:
        query = query.filter(Rental.property.capacidad >= cant_personas)

    alquileres = query.all()
    return render_template("Reservacion/rentals.html", rentals=alquileres)

@bp.route("/alquiler/<int:rental_id>")
def ver_alquiler(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    reseñas = rental.reviews  # Suponiendo que hay una relación `reviews` en Rental

    return render_template("Reservacion/show_rental.html", rental=rental, reseñas=reseñas)

@bp.route("/alquilar/<int:rental_id>", methods=["GET", "POST"])
@login_required
def alquilar(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    compañeros = Compañero.query.filter_by(user_id=current_user.id).all()
    reservas = Reservation.query.filter_by(rental_id=rental_id).all()
    dias_ocupados = [(r.start_date, r.end_date) for r in reservas]

    if request.method == "POST":
        # Obtener fechas de la reserva
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        payment_method_id = current_user.stripe_payment_method_id

        # Validaciones básicas de fechas
        if not start_date_str or not end_date_str:
            flash("Debés elegir fecha de inicio y fin.", "warning")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Formato de fecha inválido.", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

        if start_date > end_date:
            flash("La fecha de inicio no puede ser posterior a la fecha de fin.", "warning")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

        # Validar superposición con reservas existentes
        for ocupado_inicio, ocupado_fin in dias_ocupados:
            if start_date <= ocupado_fin and end_date >= ocupado_inicio:
                flash(f"Las fechas elegidas se superponen con una reserva existente del {ocupado_inicio.strftime('%d/%m/%Y')} al {ocupado_fin.strftime('%d/%m/%Y')}.", "danger")
                return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

        # Validar método de pago
        if not payment_method_id or not isinstance(payment_method_id, str):
            flash("Método de pago inválido.", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

        # Obtener acompañantes seleccionados
        acompañantes_ids = request.form.getlist("compañeros")
        acompañantes_seleccionados = Compañero.query.filter(
            Compañero.id.in_(acompañantes_ids), Compañero.user_id == current_user.id
        ).all()

        # Procesar nuevos acompañantes
        nuevos_nombres = request.form.getlist("nuevo_nombre[]")
        nuevos_apellidos = request.form.getlist("nuevo_apellido[]")
        nuevos_dnis = request.form.getlist("nuevo_dni[]")
        nuevos_telefonos = request.form.getlist("nuevo_telefono[]")

        nuevos_acompañantes = []
        for nombre, apellido, dni, telefono in zip(nuevos_nombres, nuevos_apellidos, nuevos_dnis, nuevos_telefonos):
            nombre = nombre.strip()
            apellido = apellido.strip()
            dni = dni.strip()
            telefono = telefono.strip()

            if nombre and apellido and dni:
                existente = Compañero.query.filter_by(dni=dni, user_id=current_user.id).first()
                if existente:
                    nuevos_acompañantes.append(existente)
                else:
                    nuevo = Compañero(
                        nombre=nombre,
                        apellido=apellido,
                        dni=dni,
                        telefono=telefono,
                        user_id=current_user.id
                    )
                    db.session.add(nuevo)
                    nuevos_acompañantes.append(nuevo)

        db.session.commit()

        # Crear la reserva en BD
        nueva_reserva = Reservation(
            start_date=start_date,
            end_date=end_date,
            price_per_night=rental.price,
            rental_id=rental.id,
            user_id=current_user.id,
            compañeros=acompañantes_seleccionados + nuevos_acompañantes
        )
        db.session.add(nueva_reserva)
        db.session.commit()

        # Procesar pago con Stripe
        try:
            # Buscar o crear cliente Stripe
            clientes = stripe.Customer.list(email=current_user.email).data
            if clientes:
                cliente = clientes[0]
            else:
                cliente = stripe.Customer.create(
                    email=current_user.email,
                    name=f"{current_user.nombre} {current_user.apellido}"
                )

            # Intentar adjuntar el método de pago
            try:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=cliente.id,
                )
            except stripe.error.InvalidRequestError:
                # Ya estaba adjunto
                pass

            # Establecer método de pago predeterminado
            stripe.Customer.modify(
                cliente.id,
                invoice_settings={"default_payment_method": payment_method_id},
            )

            # Ca
            cotizacion_usd = 1000  # Ejemplo, 1 USD = 1000 ARS
            precio_ars = rental.price  # 5000 ARS
            precio_usd = precio_ars / cotizacion_usd  # 5 USD

            noches = (end_date - start_date).days + 1
            total_a_pagar = int(precio_usd * noches * 100)
            # Crear y confirmar PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
            amount=total_a_pagar,
            currency="usd",  # o "usd" si querés, pero usá ARS para pesos argentinos
            customer=cliente.id,
            payment_method=payment_method_id,
            off_session=True,
            confirm=True,
            description=f"Reserva inmueble {rental.id} - Usuario {current_user.id}",
            )

            flash("Reserva y pago confirmados con éxito.", "success")
            return redirect(url_for("home"))

        except stripe.error.CardError as e:
            # Eliminar reserva para mantener consistencia si falla el pago
            db.session.delete(nueva_reserva)
            db.session.commit()
            flash(f"Error en el pago: {e.user_message}", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

        except Exception as e:
            db.session.delete(nueva_reserva)
            db.session.commit()
            flash(f"Error inesperado: {str(e)}", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)



@bp.route("/eliminar-compañero/<int:id>", methods=["POST"])
@login_required
def eliminar_compañero(id):
    compañero = Compañero.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(compañero)
    db.session.commit()
    flash("Acompañante eliminado.", "info")
    return redirect(request.referrer or url_for('reservation.alquilar'))
