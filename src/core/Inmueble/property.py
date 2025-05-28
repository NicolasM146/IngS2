# src/core/Propiedad/property.py
from src.core.database import db
from src.core.Usuario import User

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
    user = db.relationship('User', back_populates='properties')

    # **QUITAR rental_id y FK a rentals**

    rental = db.relationship('Rental', back_populates='property', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Property {self.id}: {self.direccion}>'
