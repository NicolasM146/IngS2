
from src.core.Alquiler.Rental import Rental
from src.core.Reserva.reservation import Reservation
from src.core.Usuario.Compañero import Compañero
from flask_login import login_required, current_user
from src.core.database import db
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for

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
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")

        if not start_date_str or not end_date_str:
            flash("Debés elegir fecha de inicio y fin.", "warning")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        if start_date > end_date:
            flash("La fecha de inicio no puede ser posterior a la fecha de fin.", "warning")
            return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

        # Validar superposición de fechas
        for ocupado_inicio, ocupado_fin in dias_ocupados:
            if start_date <= ocupado_fin and end_date >= ocupado_inicio:
                flash(f"Las fechas elegidas se superponen con una reserva existente del {ocupado_inicio.strftime('%d/%m/%Y')} al {ocupado_fin.strftime('%d/%m/%Y')}.", "danger")
                return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)

        # 1) Acompañantes seleccionados existentes
        acompañantes_ids = request.form.getlist("compañeros")
        acompañantes_seleccionados = Compañero.query.filter(Compañero.id.in_(acompañantes_ids), Compañero.user_id == current_user.id).all()

        # 2) Crear nuevos acompañantes
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
                # Validar si ya existe acompañante con ese DNI para evitar duplicados
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

        # Commit para que los nuevos acompañantes tengan ID
        db.session.commit()

        # Crear reserva
        nueva_reserva = Reservation(
            start_date=start_date,
            end_date=end_date,
            price_per_night=rental.price,  # Asumo que rental tiene precio por noche
            rental_id=rental.id,
            user_id=current_user.id,
            compañeros=acompañantes_seleccionados + nuevos_acompañantes
        )
        db.session.add(nueva_reserva)
        db.session.commit()

        flash("Reserva confirmada con éxito.", "success")
        return redirect(url_for("home"))

    return render_template("Reservacion/reservation.html", rental=rental, compañeros=compañeros, dias_ocupados=dias_ocupados)



@bp.route("/eliminar-compañero/<int:id>", methods=["POST"])
@login_required
def eliminar_compañero(id):
    compañero = Compañero.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(compañero)
    db.session.commit()
    flash("Acompañante eliminado.", "info")
    return redirect(request.referrer or url_for('reservation.alquilar'))
