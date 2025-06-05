
from src.core.Alquiler.Rental import Rental
from src.core.Reserva.reservation import Reservation
from src.core.Usuario.Compañero import Compañero
from src.core.Inmueble.property import Property
from flask_login import login_required, current_user
from src.core.database import db
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from datetime import date

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
    direccion = request.args.get("direccion", type=str)
    habitaciones = request.args.get("habitaciones", type=int)
    cant_personas = request.args.get("cant_personas", type=int)

    alquileres = []
    busqueda_realizada = False

    if request.args:  # Solo si se presionó "Buscar"
        busqueda_realizada = True
        query = Rental.query.join(Rental.property).filter(Rental.is_active == True)

        if precio_min is not None:
            query = query.filter(Rental.price >= precio_min)

        if precio_max is not None:
            query = query.filter(Rental.price <= precio_max)

        if fecha_inicio and fecha_fin:
            try:
                fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
                ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

                subquery = db.session.query(Reservation.rental_id).filter(
                    Reservation.start_date <= ff,
                    Reservation.end_date >= fi
                ).subquery()

                query = query.filter(~Rental.id.in_(subquery))
            except ValueError:
                pass

        if localidad:
            query = query.filter(Property.localidad.ilike(f"%{localidad}%"))

        if direccion:
            query = query.filter(Property.direccion.ilike(f"%{direccion}%"))

        if habitaciones:
            query = query.filter(Property.habitaciones == habitaciones)

        if cant_personas:
            query = query.filter(Property.capacidad == cant_personas)

        alquileres = query.all()

    return render_template("Reservacion/rentals.html", rentals=alquileres, busqueda_realizada=busqueda_realizada)


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
    hoy = date.today().isoformat()  # formato 'YYYY-MM-DD'
    if request.method == "POST":
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        payment_method_id = current_user.stripe_payment_method_id


        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Formato de fecha inválido.", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)

        if start_date > end_date:
            flash("La fecha de inicio no puede ser posterior a la fecha de fin.", "warning")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)

        for ocupado_inicio, ocupado_fin in dias_ocupados:
            if start_date <= ocupado_fin and end_date >= ocupado_inicio:
                flash(f"Las fechas elegidas se superponen con una reserva existente del {ocupado_inicio.strftime('%d/%m/%Y')} al {ocupado_fin.strftime('%d/%m/%Y')}.", "danger")
                return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)

        if not payment_method_id or not isinstance(payment_method_id, str):
            flash("Método de pago inválido.", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)

        acompañantes_ids = request.form.getlist("compañeros[]")
        acompañantes_ids = list(map(int, acompañantes_ids))  # 👈 esta línea es clave

        acompañantes_seleccionados = Compañero.query.filter(
        Compañero.id.in_(acompañantes_ids), Compañero.user_id == current_user.id
            ).all()

        nuevos_nombres = request.form.getlist("nuevo_nombre[]")
        nuevos_apellidos = request.form.getlist("nuevo_apellido[]")
        nuevos_dnis = request.form.getlist("nuevo_dni[]")
        nuevos_telefonos = request.form.getlist("nuevo_telefono[]")
        nuevos_nacimientos = request.form.getlist("nuevo_nacimiento[]")  # Debe venir del formulario
        nuevos_tutores = request.form.getlist("nuevo_tutor[]")
        nuevos_estados_civiles = request.form.getlist("nuevo_estado_civil[]")

        nuevos_acompañantes = []
        for nombre, apellido, dni, telefono, nacimiento,tutor,estado_civil in zip(nuevos_nombres, nuevos_apellidos, nuevos_dnis, nuevos_telefonos, nuevos_nacimientos,nuevos_tutores, nuevos_estados_civiles):
            nombre = nombre.strip()
            apellido = apellido.strip()
            dni = dni.strip()
            telefono = telefono.strip()
            nacimiento = nacimiento.strip()
            tutor = tutor.strip()
            estado_civil = estado_civil.strip()
            
            

            if nombre and apellido and dni and telefono and estado_civil:
                if dni and len(dni) < 7:
                    flash(f"DNI inválido para {nombre} {apellido}. Debe tener al menos 7 caracteres.", "warning")
                    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)
                if not nacimiento:
                    flash(f"Fecha de nacimiento requerida para {nombre} {apellido}.", "warning")
                    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)
        
                try:
                    fecha_nacimiento = datetime.strptime(nacimiento, "%Y-%m-%d").date()
                    hoy = datetime.today().date()
                    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                    if edad < 18 and not tutor:
                        flash(f"El acompañante {nombre} {apellido} es menor de edad ({edad} años).", "warning")
                        return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)
                except ValueError:
                    flash(f"Fecha de nacimiento inválida para {nombre} {apellido}.", "danger")
                    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)

                existente = Compañero.query.filter_by(dni=dni, user_id=current_user.id).first()
                if existente:
                    nuevos_acompañantes.append(existente)
                else:
                    nuevo = Compañero(
                        nombre=nombre,
                        apellido=apellido,
                        dni=dni,
                        telefono=telefono,
                        user_id=current_user.id,
                        fechaNacimiento=fecha_nacimiento,
                        estado_civil=estado_civil,
                        tutor=tutor if tutor else None  # Si es menor, asignar tutor
                    )
                    db.session.add(nuevo)
                    nuevos_acompañantes.append(nuevo)

        db.session.commit()

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

        try:
            clientes = stripe.Customer.list(email=current_user.email).data
            if clientes:
                cliente = clientes[0]
            else:
                cliente = stripe.Customer.create(
                    email=current_user.email,
                    name=current_user.nombre  # 👈 CAMBIO HECHO AQUÍ
                )

            try:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=cliente.id,
                )
            except stripe.error.InvalidRequestError:
                pass

            stripe.Customer.modify(
                cliente.id,
                invoice_settings={"default_payment_method": payment_method_id},
            )

            cotizacion_usd = 1000
            precio_ars = rental.price
            precio_usd = precio_ars / cotizacion_usd

            noches = (end_date - start_date).days + 1
            total_a_pagar = int(precio_usd * noches * 100)

            payment_intent = stripe.PaymentIntent.create(
                amount=total_a_pagar,
                currency="usd",
                customer=cliente.id,
                payment_method=payment_method_id,
                off_session=True,
                confirm=True,
                description=f"Reserva inmueble {rental.id} - Usuario {current_user.id}",
            )

            flash("Reserva Exitosa", "success")
            return redirect(url_for("home"))


        except stripe.error.CardError as e:
            # Agrego este print(e) para entender por que me da error el pago
            print(str(e) + " PRIMER PRINT")
            db.session.delete(nueva_reserva)
            db.session.commit()
            flash("Error en el pago, no se realizo la reserva", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)

        except Exception as e:
            # Agrego este print(e) para entender por que me da error el pago
            print(str(e) + " SEGUNDO PRINT")
            db.session.delete(nueva_reserva)
            db.session.commit()
            flash("Error en el pago, no se realizo la reserva", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados,hoy=hoy)

    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)


@bp.route("/eliminar-compañero/<int:id>/<int:rental_id>", methods=["POST"])

@login_required
def eliminar_compañero(id, rental_id):
    compañero = Compañero.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if len(compañero.reservas) > 0:
        compañero.user_id = None
        db.session.commit()
        flash("El acompañante fue desvinculado de tu cuenta pero conserva historial de reservas.", "info")
    else:
        db.session.delete(compañero)
        db.session.commit()
        flash("Acompañante eliminado.", "info")

    return redirect(url_for("reservation.alquilar", rental_id=rental_id))