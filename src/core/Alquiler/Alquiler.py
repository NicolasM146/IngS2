from datetime import datetime
from src.core.database import db
from src.core.Inmueble.Inmueble import Inmueble  # Importamos el modelo Inmueble para relaciones

class Alquiler(db.Model):
    __tablename__ = 'alquileres'  # Nombre de la tabla en PostgreSQL

    # --- Columnas principales ---
    id = db.Column(db.Integer, primary_key=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)  # Fecha de creación automática
    precio = db.Column(db.Float, nullable=False)  # Precio por noche
    descripcion = db.Column(db.Text)  # Descripción opcional
    esta_activo = db.Column(db.Boolean, default=True)  # Para bloquear/liberar alquileres

    # --- Relaciones ---
    # 1:1 con Inmueble (un alquiler pertenece a UN inmueble)
    inmueble_id = db.Column(db.Integer, db.ForeignKey('inmuebles.id'), unique=True, nullable=False)
    # 'inmueble_asociado' es el backref desde Inmueble (no se declara aquí)

    # 1:N con Reserva (un alquiler puede tener muchas reservas)
    reservas = db.relationship('Reserva', backref='alquiler', lazy='dynamic', cascade='all, delete-orphan')

    # 1:N con Reseña (un alquiler puede tener muchas reseñas)
    reseñas = db.relationship('Reseña', backref='alquiler', lazy='dynamic')

    # --- Métodos ---
    def __repr__(self):
        return f'<Alquiler ID: {self.id}, Inmueble: {self.inmueble_id}>'

    def to_json(self):
        return {
            "id": self.id,
            "precio": self.precio,
            "inmueble_id": self.inmueble_id,
            "esta_activo": self.esta_activo
        }