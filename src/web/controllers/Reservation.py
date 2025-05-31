from flask import Blueprint, render_template, request
from src.core.Alquiler.Rental import Rental
from src.core.Reserva.reservation import Reservation
from src.core.database import db
from datetime import datetime

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
