

from src.core.database import db
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from src.core.Usuario.Roles_y_Permisos import Permiso
from flask_login import UserMixin
from src.core.Inmueble.property import Property
from src.core.Usuario.Compañero import Compañero


class User(UserMixin,db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    dni = db.Column(db.String(15), unique=True, nullable=False)
    nacionalidad = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    es_sysadmin = db.Column(db.Boolean, nullable=False)
    # Campo para indicar si el usuario confirmo su email
    email_confirmed = db.Column(db.Boolean, default=False)
    # Campo para indicar si el usuario está bloqueado
    is_locked = db.Column(db.Boolean, default=False, nullable=False)

    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    rol = db.relationship("Rol", back_populates="usuarios")
    
    # Relacion con la clase Property
    
    properties = db.relationship('Property', back_populates='user')
    
    # Relacion con la clase Review
    reviews = db.relationship('Review', back_populates='user')
    
    
    stripe_payment_method_id = db.Column(db.String(255), unique=True, nullable=True)
    
    # Relaion con reservation
    reservations = db.relationship('Reservation', back_populates='user', lazy='dynamic')

    compañeros = db.relationship('Compañero', back_populates='user')  



    def es_mayor_de_edad(self):
        today = date.today()
        edad = today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
        return edad >= 18

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def bloquear(self):
        self.is_locked = True

    def desbloquear(self):
        self.is_locked = False

    def tiene_permiso(self, nombre_permiso):
        """
        if self.es_sysadmin:
            permiso = Permiso.query.filter_by(nombre=nombre_permiso).first()
            if not permiso:
                raise ValueError(f"El permiso {nombre_permiso} no existe")
            return True
        if self.rol is None:
            return False
        return self.rol.tiene_permiso(nombre_permiso)
        """
        return True
    def __repr__(self):
        return f'<User {self.username}>'
