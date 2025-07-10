from datetime import datetime
from src.core.database import db

reserva_compañero = db.Table(
    'reserva_compañero',
    db.Column('reservation_id', db.Integer, db.ForeignKey('reservations.id'), primary_key=True),
    db.Column('compañero_id', db.Integer, db.ForeignKey('compañeros.id'), primary_key=True)
)

class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pendiente') # Pendiente, Vigente, terminada, cancelada
    advance_payment = db.Column(db.Boolean, default=False)

    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'), nullable=False)
    rental = db.relationship("Rental", back_populates="reservations")

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User", back_populates="reservations")

    compañeros = db.relationship(
        'Compañero',
        secondary=reserva_compañero,
        back_populates='reservas'
    )

    # backref desde UpgradeRequest con passive_deletes=True (ver abajo)
    upgrade_requests_old = db.relationship(
        'UpgradeRequest',
        back_populates='old_reservation',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def esta_vigente(self) -> bool:
        hoy = datetime.utcnow().date()
        return self.start_date <= hoy <= self.end_date
