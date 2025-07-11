from src.core.database import db
from src.core.Inmueble.property import Localidad

def cargar_localidades():
    localidades_lista = [
    "Buenos Aires", "Córdoba", "Rosario", "Mendoza", "Tucumán",
    "La Plata", "Mar del Plata", "Salta", "Resistencia", "Santiago del Estero",
    "Corrientes", "Bahía Blanca", "Paraná", "Neuquén", "Posadas",
    "San Salvador de Jujuy", "San Juan", "Santa Fe", "Comodoro Rivadavia", "Quilmes",
    "Godoy Cruz", "Lanús", "Ezeiza", "Las Heras", "La Rioja",
    "San Luis", "Ituzaingó", "Río Cuarto", "Concordia", "Berisso",
    "San Miguel", "San Martín de los Andes", "Villa María", "Morón", "Adrogué",
    "Neuquén", "Olavarría", "Junín", "Tandil", "Chivilcoy",
    "Pergamino", "Necochea", "Lanús Oeste", "San Nicolás", "San Rafael",
    "Bariloche", "Formosa", "Santa Rosa", "Zárate", "Tigre",
    "Trelew", "Río Gallegos", "San Fernando", "San Fernando del Valle de Catamarca",
    "Pilar", "Campana", "Ushuaia", "Villa Gesell", "Viedma",
    "Miramar", "Pinamar", "Marcos Paz", "Sunchales", "Villa Mercedes",
    "Rawson", "Zapala", "Cutral Có", "Junín de los Andes", "Luján",
    "Esquel", "Las Flores", "Baradero", "Chascomús", "Ayacucho",
    "Dolores", "Carlos Paz", "San Isidro", "La Banda", "Río Cuarto",
    "Grand Bourg", "Merlo", "Granadero Baigorria", "Villa Regina", "Chajarí",
    "Puerto Iguazú", "Granadero Baigorria", "Tapalqué", "Gualeguaychú", "Goya",
    "Reconquista", "Catamarca", "San Lorenzo", "Almirante Brown", "Virrey del Pino",
    "Villa Carlos Paz", "Godoy Cruz", "Malvinas Argentinas", "San Justo",
    "Bernal", "Florida", "Billinghurst", "Longchamps", "Tigre",
    "Escobar", "Pilar", "Morón", "Lanús", "Quilmes",
    "Lomas de Zamora", "Bernal", "Avellaneda", "Luis Guillón", "Rafael Calzada",
    "Monte Grande", "Burzaco", "Temperley", "Adrogué", "Banfield",
    "Turdera", "Gregorio de Laferrère", "Villa Luzuriaga", "González Catán", "Morón",
    "Merlo", "Ituzaingó", "Moreno", "José C. Paz", "Virrey del Pino",
    "San Miguel", "San Justo", "Pilar", "Florencio Varela", "San Vicente",
    "Luján", "San Pedro", "Dolores", "Chacabuco", "Junín",
    "Pergamino", "Tandil", "Necochea", "Bahía Blanca", "Olavarría",
    "Mar del Plata", "Tandil", "Miramar", "Necochea", "Villa Gesell",
    "Bariloche", "San Martín", "Godoy Cruz", "Luján de Cuyo", "Guaymallén",
    "General San Martín", "Baradero", "Campana", "Garín", "Escobar",
    "Ezeiza", "Avellaneda", "Quilmes", "Temperley", "Burzaco",
]

    for nombre in localidades_lista:
        if not Localidad.query.filter_by(nombre=nombre).first():
            loc = Localidad(nombre=nombre)
            db.session.add(loc)
            print("Cargando a" + str(loc))

    db.session.commit()
    print("Localidades cargadas correctamente")
from datetime import date, timedelta
from src.core.database import db
from src.core.Usuario.User import User
from src.core.Usuario.Roles_y_Permisos import Rol
from src.core.Inmueble.property import Property
from src.core.Alquiler.Rental import Rental
from src.core.Reserva.reservation import Reservation
from src.core.Inmueble.localidad.Localidad import Localidad


def cargar_datos_prueba():

    # Obtener o crear rol Cliente
    rol_cliente = Rol.query.filter_by(nombre="Cliente").first()
    if not rol_cliente:
        rol_cliente = Rol(nombre="Cliente")
        db.session.add(rol_cliente)
        db.session.commit()

    # Usuario cliente (sin método de pago, no importa)
    user_cliente = User.query.filter_by(email="cliente_prueba@example.com").first()
    if not user_cliente:
        user_cliente = User(
            nombre="ClientePrueba",
            dni="11111111",
            nacionalidad="Argentina",
            email="cliente_prueba@example.com",
            telefono="000000000",
            fecha_nacimiento=date(1990,1,1),
            username="clientetest",
            es_sysadmin=False,
            rol=rol_cliente
        )
        user_cliente.set_password("password123")
        db.session.add(user_cliente)
        db.session.commit()

    # Localidad y propiedad
    loc_baires = Localidad.query.filter_by(nombre="Buenos Aires").first()
    if not loc_baires:
        loc_baires = Localidad(nombre="Buenos Aires")
        db.session.add(loc_baires)
        db.session.commit()

    prop = Property.query.filter_by(direccion="Av. Siempre Viva 742").first()
    if not prop:
        prop = Property(
            direccion="Av. Siempre Viva 742",
            localidad=loc_baires,
            user=user_cliente
        )
        db.session.add(prop)
        db.session.commit()

    rental = Rental.query.filter_by(property_id=prop.id).first()
    if not rental:
        rental = Rental(
            property_id=prop.id,
            description="Departamento para pruebas",
            price=1200
        )
        db.session.add(rental)
        db.session.commit()

    hoy = date.today()

    # Reserva CONFIRMADA que empieza HOY (debería pasar a VIGENTE)
    reserva_confirmada = Reservation.query.filter_by(
        user_id=user_cliente.id,
        rental_id=rental.id,
        status="Confirmada",
        start_date=hoy
    ).first()
    if not reserva_confirmada:
        reserva_confirmada = Reservation(
            start_date=hoy,
            end_date=hoy + timedelta(days=2),
            status="Confirmada",
            price_per_night=1200,
            advance_payment=True,
            user=user_cliente,
            rental=rental
        )
        db.session.add(reserva_confirmada)

    # Reserva VIGENTE que terminó AYER (debería pasar a TERMINADA)
    reserva_vigente = Reservation.query.filter_by(
        user_id=user_cliente.id,
        rental_id=rental.id,
        status="Vigente",
        end_date=hoy - timedelta(days=1)
    ).first()
    if not reserva_vigente:
        reserva_vigente = Reservation(
            start_date=hoy - timedelta(days=4),
            end_date=hoy - timedelta(days=1),
            status="Vigente",
            price_per_night=1100,
            advance_payment=False,
            user=user_cliente,
            rental=rental
        )
        db.session.add(reserva_vigente)

    db.session.commit()
    print("✅ Reservas Confirmada y Vigente cargadas para pruebas sin pendientes.")

if __name__ == "__main__":
    from src.web import create_app
    app = create_app()
    with app.app_context():
        cargar_localidades()
        cargar_datos_prueba()


