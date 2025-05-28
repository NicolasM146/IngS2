from datetime import datetime
from src.core.database import db

class Rental(db.Model):
    __tablename__ = 'rentals'

    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), unique=True, nullable=False)

    property = db.relationship("Property", back_populates="rental", foreign_keys=[property_id])

    # Para Review y Reservation, asegurate que también estén importados al final
    reviews = db.relationship("Review", back_populates="rental", cascade='all, delete-orphan')
    reservations = db.relationship("Reservation", back_populates="rental", lazy='dynamic', cascade='all, delete-orphan')

# IMPORTAR Property AL FINAL PARA EVITAR CICLO DE IMPORTACION
from src.core.Inmueble.property import Property

# IMPORTAR Review y Reservation también al final para romper ciclos
from src.core.Resenia.Review import Review
from src.core.Reserva.reservation import Reservation
