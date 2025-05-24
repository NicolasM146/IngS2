from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from src.core.Usuario.User import User
from src.core.database import db

bp = Blueprint("login", __name__, url_prefix="/login")


@bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("El email no está registrado.", "error")
            return render_template("auth/login.html", email=email)

        if not user.check_password(password):
            flash("Contraseña incorrecta.", "error")
            return render_template("auth/login.html", email=email)

        if not user.email_confirmed:
            flash("Debes confirmar tu correo antes de iniciar sesión.", "error")
            return render_template("auth/login.html", email=email)

        if user.is_locked:
            flash("Tu cuenta está bloqueada. Contactá al administrador.", "error")
            return render_template("auth/login.html", email=email)

        # Si pasó todas las validaciones
        login_user(user)  # Guarda la sesión
        flash(f"Bienvenido {user.username}!", "success")

        # Redirigí a donde quieras (por ej: home, dashboard)
        return redirect(url_for("home"))

    return render_template("auth/login.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login.login"))
