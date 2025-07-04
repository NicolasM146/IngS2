from datetime import datetime
from src.core.database import db

class UpgradeRequest(db.Model):
    __tablename__ = 'upgrade_requests'

    id = db.Column(db.Integer, primary_key=True)

    old_reservation_id = db.Column(
        db.Integer,
        db.ForeignKey('reservations.id', ondelete='CASCADE'),
        nullable=False
    )

    new_rental_id = db.Column(
        db.Integer,
        db.ForeignKey('rentals.id'),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted = db.Column(db.Boolean, nullable=True)  # None = pendiente, True/False = respuesta del cliente

    old_reservation = db.relationship(
        "Reservation",
        back_populates="upgrade_requests_old",
        foreign_keys=[old_reservation_id],
        passive_deletes=True
    )

    new_rental = db.relationship("Rental", foreign_keys=[new_rental_id])
