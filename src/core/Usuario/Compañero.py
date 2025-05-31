from src.core.database import db

class Compañero(db.Model):
    __tablename__ = 'compañeros'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    apellido = db.Column(db.String(120), nullable=False)
    dni = db.Column(db.String(15), unique=True, nullable=False)
    estado_civil = db.Column(db.String(50), nullable=True)
    telefono = db.Column(db.String(20), nullable=False)

    # ForeignKey hacia User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='compañeros')

    def __repr__(self):
        return f'<Compañero {self.nombre} {self.apellido} - DNI: {self.dni}>'
