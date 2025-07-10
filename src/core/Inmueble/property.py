from src.core.database import db
from src.core.Inmueble.localidad.Localidad import Localidad

class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(db.Integer, primary_key=True)
    direccion = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    # Estados posibles: disponible, baja, ocupado (ocupado si esta alquilado y ocupado al momento de la consulta)
    estado = db.Column(db.String(20), default='disponible') # disponible, publicado, baja, bloqueado (cuando bloqueas el alquiler)
    capacidad = db.Column(db.Integer)
    habitaciones = db.Column(db.Integer)
    
    localidad_id = db.Column(db.Integer, db.ForeignKey('localidad.id'), nullable=False)
    localidad = db.relationship('Localidad')


    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User", back_populates="properties")

    photos = db.relationship("PropertyPhoto", back_populates="property", cascade='all, delete-orphan')
    
    rentals = db.relationship("Rental", back_populates="property", cascade='all, delete-orphan')

@property
def rental(self):
    return next((r for r in self.rentals if r.is_active), None)

@property
def puede_ser_eliminado(self):
    return self.estado in ['disponible', 'baja'] and all(r.reservations.count() == 0 for r in self.rentals)

@property
def puede_darse_de_baja(self):
    return self.estado in ['disponible']

# IMPORTAR Rental AL FINAL PARA EVITAR CICLO DE IMPORTACION
from src.core.Alquiler.Rental import Rental