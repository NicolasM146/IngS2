from flask import session
from flask import redirect
from flask import url_for
from functools import wraps
from flask import flash
from src.core.Usuario import User


def is_authenticated(session):
    """
    Retorna True/False dependiendo de si la sesión está asociada a un usuario.
    """
    return session.get("user") is not None


def login_required(f):
    """
    Versión decorator de is_authenticated. Redirige a login si no hay un usuario asociado a la sesión.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated(session):
            flash("Debes iniciar sesión para acceder a esta página", "info")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated_function


def tiene_permiso(session, permiso):
    """
    Retorna True si el usuario de la sesión actual tiene el permiso dado. False en caso contrario.
    Lanza una excepción si el permiso no existe (a no ser que no haya un usuario en la sesión).
    """
    if not is_authenticated(session):
        return False
    user_id = session.get("user")
    user = User.query.get(user_id)
    if user is not None:
        return user.tiene_permiso(permiso)
    else:
        return False


def permiso_required(permiso):
    """
    Versión decorator de tiene_permiso. Redirige a home si el usuario asociado a la sesión no tiene el permiso dado.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not tiene_permiso(session, permiso):
                flash("No tienes permiso para acceder a esta página", "info")
                return redirect(url_for("home"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator
