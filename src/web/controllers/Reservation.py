
from src.core.Alquiler.Rental import Rental
from src.core.Reserva.reservation import Reservation
from src.core.Usuario.Compañero import Compañero
from src.core.Inmueble.property import Property
from flask_login import login_required, current_user
from src.core.database import db
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for
from datetime import date
from statistics import mean
from collections import Counter
from src.core.Inmueble.localidad.Localidad import Localidad
from src.core.Usuario.User import User
from src.web.handlers.auth import permiso_required

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
    localidad_id = request.args.get("localidad_id", type=int)
    direccion = request.args.get("direccion", type=str)
    habitaciones = request.args.get("habitaciones", type=int)
    cant_personas = request.args.get("cant_personas", type=int)

    localidades = Localidad.query.order_by(Localidad.nombre).all()
    alquileres = []
    busqueda_realizada = False

    if request.args:
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

        if localidad_id:
            query = query.filter(Property.localidad_id == localidad_id)

        if direccion:
            query = query.filter(Property.direccion.ilike(f"%{direccion}%"))

        if habitaciones:
            query = query.filter(Property.habitaciones == habitaciones)

        if cant_personas:
            query = query.filter(Property.capacidad == cant_personas)

        alquileres = query.all()

    return render_template(
        "Reservacion/rentals.html",
        rentals=alquileres,
        localidades=localidades,
        busqueda_realizada=busqueda_realizada,
        request_args=request.args  # para mantener los valores seleccionados
    )


# No se deberia usar esta funcion, existe show() en el controlador rental.
@bp.route("/alquiler/<int:rental_id>")
def ver_alquiler(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    reviews = rental.reviews  # Relación definida en el modelo Rental

    # Calcular promedio de puntuación
    if reviews:
        average_rating = round(mean([r.stars for r in reviews if r.stars is not None]), 2)
    else:
        average_rating = 0

    # Contar cuántas reseñas hay por cada cantidad de estrellas
    review_summary = Counter(r.stars for r in reviews if r.stars is not None)

    return render_template(
        "Reservacion/show_rental.html",
        rental=rental,
        reviews=reviews,
        average_rating=average_rating,
        review_summary=review_summary,
    )

@bp.route("/alquilar/<int:rental_id>", methods=["GET", "POST"])
@login_required
def alquilar(rental_id):
    # Obtiene el alquiler según el ID recibido
    rental = Rental.query.get_or_404(rental_id)

    # Trae todos los compañeros (acompañantes previamente guardados) asociados al usuario actual
    compañeros = Compañero.query.filter_by(user_id=current_user.id).all()

    # Trae todas las reservas asociadas a ese alquiler
    reservas = Reservation.query.filter_by(rental_id=rental_id).all()

    # Crea una lista con tuplas (inicio, fin) de las fechas ocupadas
    dias_ocupados = [(r.start_date, r.end_date) for r in reservas]

    # Obtiene la fecha actual como string ISO (formato 'YYYY-MM-DD') para usar como mínimo en inputs
    hoy = date.today().isoformat()

    # Si es un POST, entonces se está enviando una reserva
    if request.method == "POST":
        # Se obtienen las fechas ingresadas desde el formulario
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")

        # Se obtiene el método de pago que tiene el usuario guardado (usado con Stripe)
        payment_method_id = current_user.stripe_payment_method_id
        user_reservation_id = current_user.id

        users = []
        if current_user.es_sysadmin:
            users = User.query.order_by(User.nombre).all()

        if current_user.es_sysadmin:
            compañeros = []  # vacío al cargar
        else:
            compañeros = Compañero.query.filter_by(is_locked=False).all()

        if current_user.es_sysadmin:
            user_reservation_id = request.form.get("user_reservation_id", type=int)
            if not user_reservation_id:
                flash("Debe seleccionar un usuario para asignar la reserva.", "warning")
        else:
            user_reservation_id = current_user.id

        # Intenta convertir las fechas a objetos `date`, muestra error si el formato es inválido
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Formato de fecha inválido.", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)

        # Valida que las fechas sean correctas
        if start_date >= end_date:
            flash("La fecha de inicio no puede ser posterior o igual a la fecha de fin.", "warning")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)

        # Valida que no se superpongan las fechas con reservas ya existentes
        for ocupado_inicio, ocupado_fin in dias_ocupados:
            if start_date <= ocupado_fin and end_date >= ocupado_inicio:
                flash(f"Las fechas elegidas se superponen con una reserva existente del {ocupado_inicio.strftime('%d/%m/%Y')} al {ocupado_fin.strftime('%d/%m/%Y')}.", "danger")
                return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)

        # Valida que el método de pago sea válido
        if not payment_method_id or not isinstance(payment_method_id, str):
            flash("Método de pago inválido.", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)

        # Se obtienen los IDs de los acompañantes seleccionados ya existentes
        acompañantes_ids = list(map(int, request.form.getlist("compañeros[]")))

        # Se obtienen los objetos Compañero correspondientes a esos IDs
        acompañantes_seleccionados = Compañero.query.filter(
            Compañero.id.in_(acompañantes_ids), Compañero.user_id == current_user.id
        ).all()

        # Se obtienen los datos ingresados para nuevos acompañantes desde el formulario
        nuevos_nombres = request.form.getlist("nuevo_nombre[]")
        nuevos_apellidos = request.form.getlist("nuevo_apellido[]")
        nuevos_dnis = request.form.getlist("nuevo_dni[]")
        nuevos_telefonos = request.form.getlist("nuevo_telefono[]")
        nuevos_nacimientos = request.form.getlist("nuevo_nacimiento[]")
        nuevos_tutores = request.form.getlist("nuevo_tutor_hidden[]")
        nuevos_estados_civiles = request.form.getlist("nuevo_estado_civil[]")

        nuevos_acompañantes = []  # Lista para guardar los nuevos acompañantes a crear

        # Log bug
        print("nuevos_nombres:", nuevos_nombres)
        print("nuevo_apellido[]:", request.form.getlist("nuevo_apellido[]"))
        # Itera sobre todos los acompañantes nuevos recibidos del formulario
        for nombre, apellido, dni, telefono, nacimiento, tutor, estado_civil in zip(
            nuevos_nombres, nuevos_apellidos, nuevos_dnis, nuevos_telefonos,
            nuevos_nacimientos, nuevos_tutores, nuevos_estados_civiles
        ):
            # Elimina espacios sobrantes
            nombre = nombre.strip()
            apellido = apellido.strip()
            dni = dni.strip()
            telefono = telefono.strip()
            nacimiento = nacimiento.strip()
            tutor = tutor.strip()
            estado_civil = estado_civil.strip()

            # Log para el bug
            print("Datos recibidos: Nombre {}, Apellido {}, DNI {dni}, Telefono {telefono}, Nacimiento {nacimiento}, Tutor {tutor}, Estado civil {estado_civil}.")
            # Si alguno de estos campos obligatorios está vacío, se salta este acompañante
            if not all([nombre, apellido, dni, telefono, nacimiento, estado_civil]):
                continue

            # Intenta convertir la fecha de nacimiento a tipo date
            try:
                fecha_nacimiento = datetime.strptime(nacimiento, "%Y-%m-%d").date()
                hoy_fecha = datetime.today().date()
                edad = hoy_fecha.year - fecha_nacimiento.year - ((hoy_fecha.month, hoy_fecha.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            except ValueError:
                flash(f"Fecha de nacimiento inválida para {nombre} {apellido}.", "danger")
                return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)

            # Si el acompañante es menor de edad, se valida la existencia de tutor
            if edad < 18:
                if not tutor:
                    flash(f"El acompañante {nombre} {apellido} es menor de edad ({edad} años).", "warning")
                    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)

                # Si el tutor seleccionado es el usuario actual, se convierte a string
                if tutor == "current_user":
                    tutor_str = f"{current_user.nombre} {current_user.apellido}"
                else:
                    tutor_str = tutor

                # Verifica que el tutor exista en los acompañantes seleccionados o nuevos
                tutor_valido = any(
                    f"{c.nombre} {c.apellido}" == tutor_str for c in acompañantes_seleccionados + nuevos_acompañantes
                )
                if not tutor_valido:
                    flash(f"El tutor {tutor_str} no es válido o fue eliminado.", "danger")
                    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)
            else:
                tutor_str = None  # No se necesita tutor si es mayor de edad

            # Verifica si el acompañante ya existe (por DNI + user_id)
            existente = Compañero.query.filter_by(dni=dni, user_id=current_user.id).first()
            if existente:
                nuevos_acompañantes.append(existente)  # Si existe, se reutiliza
            else:
                # Si no existe, se crea el nuevo acompañante
                nuevo = Compañero(
                    nombre=nombre,
                    apellido=apellido,
                    dni=dni,
                    telefono=telefono,
                    user_id=user_reservation_id,
                    fechaNacimiento=fecha_nacimiento,
                    estado_civil=estado_civil,
                    tutor=tutor_str
                )
                print(f"Creando nuevo compañero: {nombre} {apellido} - DNI: {dni}") # Log creado para resolver bug
                db.session.add(nuevo)  # Se agrega a la sesión de la base de datos
                nuevos_acompañantes.append(nuevo)  # Se guarda en la lista

        db.session.commit()  # Commit para guardar los nuevos acompañantes en la base
        print("Se hizo commit de los nuevos compañeros") # Log bug

        # Se crea la reserva y se le asignan los acompañantes (existentes + nuevos)
        nueva_reserva = Reservation(
            start_date=start_date,
            end_date=end_date,
            price_per_night=rental.price,
            rental_id=rental.id,
            user_id=user_reservation_id,
            compañeros=acompañantes_seleccionados + nuevos_acompañantes,
            advance_payment=rental.advance_payment
        )
        db.session.add(nueva_reserva)
        db.session.commit()  # Se guarda la reserva

        # Inicia el proceso de cobro con Stripe
        try:
            # Busca o crea el cliente de Stripe
            clientes = stripe.Customer.list(email=current_user.email).data
            cliente = clientes[0] if clientes else stripe.Customer.create(email=current_user.email, name=current_user.nombre)

            # Intenta asociar el método de pago al cliente
            try:
                stripe.PaymentMethod.attach(payment_method_id, customer=cliente.id)
            except stripe.error.InvalidRequestError:
                pass  # Si ya está asociado, ignora el error

            # Define el método de pago por defecto
            stripe.Customer.modify(cliente.id, invoice_settings={"default_payment_method": payment_method_id})

            # Se simula cotización de dólar y se calcula el pago por noche
            cotizacion_usd = 1000
            precio_usd = rental.price / cotizacion_usd
            noches = (end_date - start_date).days + 1

            # Si se requiere adelanto, se cobra el 20%
            if rental.advance_payment:
                total_a_pagar = int(precio_usd * noches * 100 * 0.2)
                stripe.PaymentIntent.create(
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

        # Si el pago falla, se cancela la reserva creada
        except Exception as e:
            print(str(e))
            db.session.delete(nueva_reserva)
            db.session.commit()
            flash("Error en el pago, no se realizó la reserva", "danger")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)
    users = []
    if current_user.es_sysadmin:
        users = User.query.filter_by(is_locked=False).order_by(User.nombre).all()

    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy, users = users)
    # Si es GET, renderiza el formulario de reserva
    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados, hoy=hoy)


@bp.route("/eliminar-compañero/<int:id>/<int:rental_id>", methods=["POST"])
@login_required
def eliminar_compañero(id, rental_id):
    compañero = Compañero.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    nombre_compañero = f"{compañero.nombre} {compañero.apellido}"

    # Actualizar todos los acompañantes que tenían a este como tutor
    acompañantes_con_este_tutor = Compañero.query.filter(
        Compañero.tutor == nombre_compañero,
        Compañero.user_id == current_user.id
    ).all()
    
    for a in acompañantes_con_este_tutor:
        a.tutor = None
    
    if len(compañero.reservas) > 0:
        compañero.user_id = None
        db.session.commit()
        flash("El acompañante fue desvinculado de tu cuenta pero conserva historial de reservas. Se han actualizado los tutores relacionados.", "info")
    else:
        db.session.delete(compañero)
        db.session.commit()
        flash("Acompañante eliminado. Se han actualizado los tutores relacionados.", "info")

    return redirect(url_for("reservation.alquilar", rental_id=rental_id))

@bp.route("/acompañantes-usuario/<int:user_id>")
@login_required
def acompanantes_usuario(user_id):
    # Solo admin puede acceder
    if not current_user.es_sysadmin:
        return {"error": "No autorizado"}, 403

    acompañantes = Compañero.query.filter_by(user_id=user_id).all()
    data = [
        {"id": c.id, "nombre": c.nombre, "apellido": c.apellido, "dni": c.dni}
        for c in acompañantes
    ]
    return {"acompañantes": data}

