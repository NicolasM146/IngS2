from datetime import datetime
from src.core.database import db

class Compañero(db.Model):
    __tablename__ = 'compañeros'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    apellido = db.Column(db.String(120), nullable=False)
    dni = db.Column(db.String(15), unique=True, nullable=False)
    estado_civil = db.Column(db.String(50), nullable=True)
    telefono = db.Column(db.String(20), nullable=False)
    fechaNacimiento = db.Column(db.String(20), nullable=False)
    
    tutor = db.Column(db.String(250), nullable=True)  # nuevo campo tutor

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', back_populates='compañeros')

    reservas = db.relationship(
        'Reservation',
        secondary='reserva_compañero',
        back_populates='compañeros'
    )

    def es_menor_de_edad(self):
        try:
            fecha_nac = datetime.strptime(self.fechaNacimiento, "%Y-%m-%d")
        except ValueError:
            return False
        hoy = datetime.today()
        edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
        return edad < 18
