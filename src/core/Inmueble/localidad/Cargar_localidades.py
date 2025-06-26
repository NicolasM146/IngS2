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

if __name__ == "__main__":
    from src.web import create_app
    app = create_app()
    with app.app_context():
        cargar_localidades()