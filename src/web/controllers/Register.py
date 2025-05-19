from src.core.database import db
from src.core.Usuario.Roles_y_Permisos import Rol
from src.core.Usuario.User import User, Card
from datetime import datetime
from flask import flash, redirect, url_for

def registrar_usuario(data_usuario, data_tarjeta=None):
    """
    data_usuario: dict con campos para User
    data_tarjeta: dict con campos para Card, opcional
    """

    # Buscar el rol 'client'
    rol_cliente = Rol.query.filter_by(nombre="client").first()
    if not rol_cliente:
        raise Exception("El rol 'client' no está definido en la base de datos.")

    # Crear usuario
    nuevo_usuario = User(
        nombre=data_usuario.get("nombre"),
        dni=data_usuario.get("dni"),
        nacionalidad=data_usuario.get("nacionalidad"),
        email=data_usuario.get("email"),
        telefono=data_usuario.get("telefono"),
        fecha_nacimiento=datetime.strptime(data_usuario.get("fecha_nacimiento"), "%Y-%m-%d").date(),
        username=data_usuario.get("username"),
        es_sysadmin=False,
        rol=rol_cliente,
    )

    # Setear password encriptada
    nuevo_usuario.set_password(data_usuario.get("password"))

    # Validar mayor de edad (opcional)



    if not nuevo_usuario.es_mayor_de_edad():
        flash("El usuario debe ser mayor de edad para registrarse.", "error")
        return redirect(url_for('home'))  # Cambiá 'home' por el nombre real de tu ruta principal

    # ... resto del código ...

    # Si vienen datos de tarjeta, crearla y relacionarla
    if data_tarjeta:
        nueva_tarjeta = Card(
            number=data_tarjeta.get("number"),
            expiration_date=datetime.strptime(data_tarjeta.get("expiration_date"), "%Y-%m-%d").date(),
            cvv=data_tarjeta.get("cvv"),
            user=nuevo_usuario,
        )
        db.session.add(nueva_tarjeta)

    # Guardar usuario (y tarjeta si hay)
    db.session.add(nuevo_usuario)
    db.session.commit()

    return nuevo_usuario
