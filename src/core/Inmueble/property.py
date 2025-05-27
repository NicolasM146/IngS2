from src.core.database import db
from src.core.Alquiler import Rental
from src.core.Usuario import User

class Property(db.Model):
    __tablename__ = 'properties'  # Nombre de la tabla en la base de datos

    id = db.Column(db.Integer, primary_key=True)
    direccion = db.Column(db.String(255), nullable=False)
    localidad = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), default='disponible')
    capacidad = db.Column(db.Integer)
    habitaciones = db.Column(db.Integer)
    
    # En Property
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='properties')

    
    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'), nullable=False)
    rental = db.relationship("Rental", back_populates="property", foreign_keys="[Rental.property_id]")
    

    def __repr__(self):
        return f'<Property {self.id}: {self.direccion}>'
