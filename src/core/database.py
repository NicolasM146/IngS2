from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_app(app):
    """Inicializa a la base de datos con la aplicación de Flask."""
    db.init_app(app)
    config(app)

    return app


def config(app):
    """
    Configuración de hooks para la base de datos.
    """

    @app.teardown_appcontext
    def close_session(exception=None):
        db.session.remove()

    return app


def reset():
    """Resetea la base de datos."""
    print("Importando modelos...")
    # Importá acá todos los modelos para que SQLAlchemy los conozca antes de eliminar/crear tablas
    from src.core.Usuario import User
    from src.core.Usuario.Roles_y_Permisos import Rol, Permiso
    from src.core.Inmueble.property import Property
    from src.core.Alquiler.Rental import Rental
    from src.core.Resenia.Review import Review  # Agregá este si usás reviews
    from src.core.Reserva.reservation import Reservation

    print("Eliminando base de datos...")
    db.drop_all()

    print("Creando base nuevamente...")
    db.create_all()

    print("¡Listo! Se han creado las siguientes tablas: ")
    print(db.metadata.tables.keys())
