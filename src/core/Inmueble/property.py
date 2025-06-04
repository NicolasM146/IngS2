from src.core.database import db

class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(db.Integer, primary_key=True)
    direccion = db.Column(db.String(255), nullable=False)
    localidad = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), default='disponible')
    capacidad = db.Column(db.Integer)
    habitaciones = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User", back_populates="properties")

    rental = db.relationship("Rental", back_populates="property", uselist=False, cascade='all, delete-orphan')
    photos = db.relationship("PropertyPhoto", back_populates="property", cascade='all, delete-orphan')

# IMPORTAR Rental AL FINAL PARA EVITAR CICLO DE IMPORTACION
from src.core.Alquiler.Rental import Rental