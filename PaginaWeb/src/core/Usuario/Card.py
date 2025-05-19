from src.core.database import db

class Tarjeta(db.Model):
    __tablename__ = 'tarjetas'

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False)
    codigo = db.Column(db.String(4), nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    usuario = db.relationship("User", back_populates="tarjeta")

    def __repr__(self):
        return f'<Tarjeta {self.numero}>'
