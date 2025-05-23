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
    print(" Eliminando base de datos...")
    db.drop_all()
    print("Creando base nuevamente...")
    from src.core.Usuario import User
    from src.core.Usuario import Card
    from src.core.Usuario.Roles_y_Permisos import Rol, Permiso
    from src.core.Inmueble.property import Property
    from src.core.Alquiler.Rental import Rental
    db.create_all()
    print("¡Listo! Se han creado las siguientes tablas: ")
    print(db.metadata.tables.keys())
