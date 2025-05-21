from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def login_required_custom(f):
    """
    Decorador para proteger rutas. Si no hay usuario logueado, redirige a login con mensaje.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión para acceder a esta página", "info")
            return redirect(url_for("login.login"))  # Cambia "login.login" por tu endpoint real
        return f(*args, **kwargs)
    return decorated_function


def tiene_permiso(permiso):
    """
    Verifica si el usuario logueado tiene un permiso dado.
    Retorna True o False.
    """
    if not current_user.is_authenticated:
        return False
    return current_user.tiene_permiso(permiso)


def permiso_required(permiso):
    """
    Decorador para proteger rutas según permiso.
    Si el usuario no tiene permiso, redirige a home con mensaje.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not tiene_permiso(permiso):
                flash("No tienes permiso para acceder a esta página", "info")
                return redirect(url_for("home"))  # Cambia "home" por tu endpoint real
            return f(*args, **kwargs)
        return decorated_function
    return decorator
