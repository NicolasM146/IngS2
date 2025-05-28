from src.core.database import db

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User", back_populates="reviews")

    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'), nullable=False)
    rental = db.relationship("Rental", back_populates="reviews")

# IMPORTAR Rental AL FINAL
from src.core.Alquiler.Rental import Rental
