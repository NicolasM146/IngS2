from src.core.database import db

class Property(db.Model):
    __tablename__ = 'propertys'  # Nombre de la tabla en la base de datos

    id = db.Column(db.Integer, primary_key=True)
    direccion = db.Column(db.String(255), nullable=False)
    localidad = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), default='disponible')
    capacidad = db.Column(db.Integer)
    habitaciones = db.Column(db.Integer)

    alquiler = db.relationship(
        'Rental',
        backref='inmueble_asociado',
        uselist=False,
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Property {self.id}: {self.direccion}>'
