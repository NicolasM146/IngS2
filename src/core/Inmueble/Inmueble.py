from src.core.database import db
from datetime import datetime

class Inmueble(db.Model):
    __tablename__ = 'inmuebles'

    # --- Columnas principales ---
    id = db.Column(db.Integer, primary_key=True)
    direccion = db.Column(db.String(255), nullable=False)
    localidad = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)  # Descripción opcional
    estado = db.Column(db.String(20), default='disponible')  # Ej: disponible, mantenimiento, baja
    capacidad = db.Column(db.Integer)  # Número de personas
    habitaciones = db.Column(db.Integer)

    # --- Relaciones ---
    alquiler = db.relationship(
        'Alquiler',
        backref='inmueble_asociado',
        uselist=False,
        cascade='all, delete-orphan'
    )

    # --- Métodos ---
    def __repr__(self):
        return f'<Inmueble {self.id}: {self.direccion}>'

    def to_json(self):
    return {
        "id": self.id,
        "direccion": self.direccion,
        "localidad": self.localidad,
        "descripcion": self.descripcion,  # Campo añadido
        "estado": self.estado,
        "capacidad": self.capacidad,
        "habitaciones": self.habitaciones,  # Campo añadido
        "alquiler_activo": bool(self.alquiler), # Devuelve si esta alquilandose el inmueble
    }