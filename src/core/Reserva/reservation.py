from datetime import datetime
from src.core.database import db
from src.core.Usuario.User import User
from src.core.Alquiler.Rental import Rental

class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')

    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'), nullable=False)
    rental = db.relationship('Rental', back_populates='reservations')  

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='reservations')

    def __repr__(self):
        return f'<Reservation {self.id} - Rental: {self.rental_id} - User: {self.user_id}>'