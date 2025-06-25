from src.core.database import db
from datetime import datetime

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    stars = db.Column(db.Integer, nullable=False)  # de 1 a 5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'), nullable=False)

    user = db.relationship('User', back_populates='reviews')
    rental = db.relationship('Rental', back_populates='reviews')

    __table_args__ = (
        db.CheckConstraint('stars >= 1 AND stars <= 5', name='check_star_range'),
    )
# IMPORTAR Rental AL FINAL
from src.core.Alquiler.Rental import Rental
