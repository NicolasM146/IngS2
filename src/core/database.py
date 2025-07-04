from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

def init_app(app):
    """Inicializa la base de datos con la app Flask."""
    db.init_app(app)
    config(app)
    return app

def config(app):
    @app.teardown_appcontext
    def close_session(exception=None):
        db.session.remove()
    return app

def reset():
    from src.core.Inmueble.localidad.Cargar_localidades import cargar_localidades
    """Resetea la base de datos: borra y crea todas las tablas."""
    print("Importando modelos...")
    # Importá todos los modelos para que SQLAlchemy los conozca
    from src.core.Usuario.User import User
    from src.core.Usuario.Roles_y_Permisos import Rol, Permiso
    from src.core.Inmueble.property import Property
    from src.core.Alquiler.Rental import Rental
    from src.core.Resenia.Review import Review
    from src.core.Reserva.reservation import Reservation
    from src.core.Inmueble.property_photo import PropertyPhoto
    from src.core.Inmueble.localidad.Localidad import Localidad

    print("Eliminando base de datos con CASCADE...")
    db.drop_all()

    print("Creando base de datos...")
    db.create_all()

    print("¡Listo! Tablas creadas:")
    
    cargar_localidades
    
    print(db.metadata.tables.keys())
