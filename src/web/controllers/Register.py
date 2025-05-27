import re
from flask import Blueprint, request, render_template, redirect, flash, url_for, current_app
from src.core.database import db
from src.core.Usuario.Roles_y_Permisos import Rol
from src.core.Usuario.User import User
from datetime import datetime, date
from src.utils.token import confirm_token
from src.utils.email import send_confirmation_email
import stripe

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

        data_tarjeta = None
        if request.form.get("number"):
            data_tarjeta = {
                "number": request.form.get("number", "").strip(),
                "expiration_date": request.form.get("expiration_date", "").strip(),
                "cvv": request.form.get("cvv", "").strip()
            }

        rol_cliente = Rol.query.filter_by(nombre="client").first()
        if not rol_cliente:
            flash("El rol 'client' no está definido en la base de datos.", "error")
            return render_template('auth/register.html', datos=data_usuario)

        if not es_nombre_valido(data_usuario["nombre"]):
            flash("El nombre solo debe contener letras y acentos.", "error")
            return render_template('auth/register.html', datos=data_usuario)

        if not data_usuario["dni"].isdigit():
            flash("El DNI debe contener solo números.", "error")
            return render_template('auth/register.html', datos=data_usuario)

        if not es_telefono_valido(data_usuario["telefono"]):
            flash("El teléfono debe contener solo números (mínimo 6 dígitos).", "error")
            return render_template('auth/register.html', datos=data_usuario)

        if not es_email_valido(data_usuario["email"]):
            flash("El email no tiene un formato válido.", "error")
            return render_template('auth/register.html', datos=data_usuario)

        if User.query.filter_by(email=data_usuario["email"]).first():
            flash("El email ya está registrado.", "error")
            return render_template('auth/register.html', datos=data_usuario)

        if User.query.filter_by(username=data_usuario["username"]).first():
            flash("El nombre de usuario ya está en uso.", "error")
            return render_template('auth/register.html', datos=data_usuario)

        if len(data_usuario["password"]) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template('auth/register.html', datos=data_usuario)

        try:
            fecha_nacimiento = datetime.strptime(data_usuario["fecha_nacimiento"], "%Y-%m-%d").date()
            if fecha_nacimiento >= date.today():
                flash("La fecha de nacimiento no puede ser en el futuro.", "error")
                return render_template('auth/register.html', datos=data_usuario)
        except ValueError:
            flash("Fecha de nacimiento inválida.", "error")
            return render_template('auth/register.html', datos=data_usuario)

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
            email_confirmed=False
        )
        nuevo_usuario.set_password(data_usuario["password"])

        if not nuevo_usuario.es_mayor_de_edad():
            flash("El usuario debe ser mayor de edad para registrarse.", "error")
            return render_template('auth/register.html', datos=data_usuario)

        if data_tarjeta:
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            try:
                exp_year, exp_month = map(int, data_tarjeta["expiration_date"].split("-"))
                payment_method = stripe.PaymentMethod.create(
                    type="card",
                    card={
                        "number": data_tarjeta["number"],
                        "exp_month": exp_month,
                        "exp_year": exp_year,
                        "cvc": data_tarjeta["cvv"],
                    },
                )
                nuevo_usuario.stripe_payment_method_id = payment_method.id
            except stripe.error.CardError as e:
                flash("Datos de tarjeta inválidos: " + e.user_message, "error")
                return render_template('auth/register.html', datos=data_usuario)
            except Exception as e:
                flash("Error al procesar la tarjeta: " + str(e), "error")
                return render_template('auth/register.html', datos=data_usuario)

        db.session.add(nuevo_usuario)
        db.session.commit()

        send_confirmation_email(nuevo_usuario.email)
        flash("Usuario registrado. Por favor revisa tu correo para confirmar tu cuenta.", "info")
        return redirect(url_for('login.login'))

    return render_template("auth/register.html")

@bp.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash("El enlace de confirmación es inválido o ha expirado.", "error")
        return redirect(url_for('register.register'))

    user = User.query.filter_by(email=email).first_or_404()

    if user.email_confirmed:
        flash("La cuenta ya fue confirmada. Por favor inicia sesión.", "info")
    else:
        user.email_confirmed = True
        db.session.commit()
        flash("¡Gracias por confirmar tu cuenta!", "success")

    return render_template("auth/login.html")
