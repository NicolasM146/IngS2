from src.core.database import db
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
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

    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    rol = db.relationship("Rol", back_populates="usuarios")

    tarjeta = db.relationship("Tarjeta", back_populates="usuario", uselist=False)

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

    def __repr__(self):
        return f'<User {self.username}>'
