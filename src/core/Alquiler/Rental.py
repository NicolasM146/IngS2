from datetime import datetime, timedelta, timezone
from src.core.database import db

class Rental(db.Model):
    __tablename__ = 'rentals'

    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    advance_payment = db.Column(db.Boolean, default=False)

    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), unique=True, nullable=False)

    property = db.relationship("Property", back_populates="rental", foreign_keys=[property_id])

    # Para Review y Reservation, asegurate que también estén importados al final
    reviews = db.relationship("Review", back_populates="rental", cascade='all, delete-orphan')
    reservations = db.relationship("Reservation", back_populates="rental", lazy='dynamic', cascade='all, delete-orphan')
    
    def is_locked(self) -> bool:
        return not self.is_active
    
    def is_busy(self) -> bool:
        # Obtenengo todas las reservas y chequeo si alguna está vigente
        for reserva in self.reservations:
            if reserva.esta_vigente():
                return True
        return False
    
    def reserved_today_or_later(self) -> bool:
        today = datetime.now(timezone.utc).date()
        tomorrow = today + timedelta(days=1)

        # Primero chequeamos si esta ocupada
        if self.is_busy(): return True

        # Luego verificamos si hay alguna reserva con start_date >= mañana (reservas futuras)
        has_future_reservation = self.reservations.filter(
            Reservation.start_date >= tomorrow
        ).count() > 0

        return has_future_reservation

# IMPORTAR Property AL FINAL PARA EVITAR CICLO DE IMPORTACION
from src.core.Inmueble.property import Property

# IMPORTAR Review y Reservation también al final para romper ciclos
from src.core.Resenia.Review import Review
from src.core.Reserva.reservation import Reservation
