from datetime import datetime
from src.core.database import db

class Rental(db.Model):
    __tablename__ = 'rentals'

    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    property_id = db.Column(db.Integer, db.ForeignKey('propertys.id'), unique=True, nullable=False)

    #   reservations = db.relationship(
  ##       backref='rental',
  #      lazy='dynamic',
  #      cascade='all, delete-orphan'
  #  )

  #  reviews = db.relationship(
  #      'Review',
  #      backref='rental',
  #      lazy='dynamic'
  #  )

    def __repr__(self):
        return f'<Rental ID: {self.id}, Property: {self.property_id}>'

    def to_json(self):
        return {
            "id": self.id,
            "price": self.price,
            "property_id": self.property_id,
            "is_active": self.is_active
        }
