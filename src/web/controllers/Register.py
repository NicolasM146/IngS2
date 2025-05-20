import re
from flask import Blueprint, request, render_template, redirect, flash, url_for
from src.core.database import db
from src.core.Usuario.Roles_y_Permisos import Rol
from src.core.Usuario.User import User, Card
from datetime import datetime, date
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

bp = Blueprint("register", __name__, url_prefix="/register")

def es_nombre_valido(nombre):
    return bool(re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñüÜ\s]+", nombre))

def es_telefono_valido(telefono):
    return bool(re.fullmatch(r"\d{6,15}", telefono))

def es_email_valido(email):
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))

@bp.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data_usuario = {
            "nombre": request.form.get("nombre", "").strip(),
            "dni": request.form.get("dni", "").strip(),
            "nacionalidad": request.form.get("nacionalidad", "").strip(),
            "telefono": request.form.get("telefono", "").strip(),
            "email": request.form.get("email", "").strip(),
            "username": request.form.get("username", "").strip(),
            "password": request.form.get("password", ""),
            "fecha_nacimiento": request.form.get("fecha_nacimiento", "")
        }

        data_tarjeta = {
            "number": request.form.get("number", "").strip(),
            "expiration_date": request.form.get("expiration_date", "").strip(),
            "cvv": request.form.get("cvv", "").strip()
        } if request.form.get("number") else None

        # Validaciones
        rol_cliente = Rol.query.filter_by(nombre="client").first()
        if not rol_cliente:
            flash("El rol 'client' no está definido en la base de datos.", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        if not es_nombre_valido(data_usuario["nombre"]):
            flash("El nombre solo debe contener letras y acentos.", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        if not data_usuario["dni"].isdigit():
            flash("El DNI debe contener solo números.", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        if not es_telefono_valido(data_usuario["telefono"]):
            flash("El teléfono debe contener solo números (mínimo 6 dígitos).", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        if not es_email_valido(data_usuario["email"]):
            flash("El email no tiene un formato válido.", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        if User.query.filter_by(email=data_usuario["email"]).first():
            flash("El email ya está registrado.", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        if len(data_usuario["password"]) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        if User.query.filter_by(username=data_usuario["username"]).first():
            flash("El nombre de usuario ya está en uso.", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        try:
            fecha_nacimiento = datetime.strptime(data_usuario["fecha_nacimiento"], "%Y-%m-%d").date()
            if fecha_nacimiento >= date.today():
                flash("La fecha de nacimiento no puede ser en el futuro.", "error")
                return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)
        except ValueError:
            flash("Fecha de nacimiento inválida.", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        nuevo_usuario = User(
            nombre=data_usuario["nombre"],
            dni=data_usuario["dni"],
            nacionalidad=data_usuario["nacionalidad"],
            email=data_usuario["email"],
            telefono=data_usuario["telefono"],
            fecha_nacimiento=fecha_nacimiento,
            username=data_usuario["username"],
            es_sysadmin=False,
            rol=rol_cliente,
        )
        nuevo_usuario.set_password(data_usuario["password"])

        if not nuevo_usuario.es_mayor_de_edad():
            flash("El usuario debe ser mayor de edad para registrarse.", "error")
            return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

        if data_tarjeta:
            try:
                expiration = datetime.strptime(data_tarjeta.get("expiration_date"), "%Y-%m-%d").date()
            except ValueError:
                flash("La fecha de expiración de la tarjeta es inválida.", "error")
                return render_template('auth/register.html', datos=data_usuario, datos_tarjeta=data_tarjeta)

            nueva_tarjeta = Card(
                number=data_tarjeta["number"],
                expiration_date=expiration,
                cvv=data_tarjeta["cvv"],
                user=nuevo_usuario,
            )
            db.session.add(nueva_tarjeta)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Usuario registrado correctamente.", "success")
        return redirect(url_for('home'))

    # GET
    return render_template('auth/register.html')
