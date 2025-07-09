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

        # En esta versión se espera recibir un payment_method_id token desde frontend (Stripe Elements)
        payment_method_id = request.form.get("payment_method_id")

        rol_cliente = Rol.query.filter_by(nombre="Cliente").first()

        
        # Validaciones usuario
        if not es_nombre_valido(data_usuario["nombre"]):
            flash("El nombre solo debe contener letras y acentos.", "error")
            return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

        dni_raw = data_usuario["dni"]
        dni_limpio = dni_raw.replace(".", "").strip()
        
        existing_user = User.query.filter_by(dni=data_usuario["dni"]).first()
        if existing_user:
            flash("Ya existe un usuario registrado con ese DNI/Documento de identidad.", "error")
            return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])


        
        if len(dni_limpio) != 8 and data_usuario["nacionalidad"] == 'Argentina':
            flash("El DNI argentino debe tener 8 dígitos.", "error")
            return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

        data_usuario["dni"] = dni_limpio
        

        if not es_email_valido(data_usuario["email"]):
            flash("El email no tiene un formato válido.", "error")
            return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])
            

        if User.query.filter_by(email=data_usuario["email"]).first():
            flash("El email ya está registrado.", "error")
            return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])
        if User.query.filter_by(username=data_usuario["username"]).first():
            flash("El nombre de usuario ya está en uso. Por favor elegí otro.", "error")
            return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

        if len(data_usuario["password"]) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

        try:
            fecha_nacimiento = datetime.strptime(data_usuario["fecha_nacimiento"], "%Y-%m-%d").date()
            if fecha_nacimiento >= date.today():
                flash("La fecha de nacimiento no puede ser en el futuro.", "error")
                return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])
        except ValueError:
            flash("Fecha de nacimiento inválida.", "error")
            return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

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
            flash("Para registrarse debe ser mayor a 18 años.", "error")
            return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

        if payment_method_id:
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            try:
                # Asociamos el payment method al cliente (en este caso usuario aún no tiene id Stripe Customer, 
                # pero podrías crear uno aquí y guardarlo)
                nuevo_usuario.stripe_payment_method_id = payment_method_id
                # Aquí podrías crear un customer en Stripe y asociarlo si lo deseas.
                # Ejemplo (opcional):
                # customer = stripe.Customer.create(email=nuevo_usuario.email, payment_method=payment_method_id)
                # nuevo_usuario.stripe_customer_id = customer.id
            except stripe.error.StripeError as e:
                flash("El número de tarjeta no es válido","error")
                return render_template('auth/register.html', datos=data_usuario, stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])

        db.session.add(nuevo_usuario)
        db.session.commit()

        send_confirmation_email(nuevo_usuario.email)
        flash("Usuario registrado. Por favor revisa tu correo para confirmar tu cuenta.", "info")
        return redirect(url_for('login.login'))

    # GET
    return render_template("auth/register.html", stripe_public_key=current_app.config['STRIPE_PUBLISHABLE_KEY'])


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
