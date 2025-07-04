from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from src.core.Usuario.User import User
from src.core.database import db
from src.utils.email import send_password_reset_email
from src.utils.token import generate_confirmation_token, confirm_token
from datetime import datetime, timedelta
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


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("El email no está registrado", "error")
            return redirect(url_for("login.login"))

        # Generar token y enviar email
        token = generate_confirmation_token(email)
        send_password_reset_email(user.email, token)
        
        flash("Se ha enviado un enlace para restablecer tu contraseña a tu correo electrónico.", "info")
        return redirect(url_for("login.login"))

    return render_template("auth/forgot_password.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = confirm_token(token)
    except:
        flash("El enlace para restablecer la contraseña es inválido o ha expirado.", "error")
        return redirect(url_for("login.forgot_password"))

    user = User.query.filter_by(email=email).first_or_404()

    if request.method == "POST":
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("auth/reset_password.html", token=token)

        if len(new_password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("auth/reset_password.html", token=token)
        # Cambiamos directamente la contraseña sin necesidad de confirmación adicional
        user.set_password(new_password)
        db.session.commit()
        
        flash("Tu contraseña ha sido actualizada correctamente. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login.login"))
    return render_template("auth/reset_password.html", token=token)
