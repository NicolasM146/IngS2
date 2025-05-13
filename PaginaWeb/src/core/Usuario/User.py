from src.core.database import db
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from src.core.Usuario.Roles_y_Permisos import Permiso


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    dni = db.Column(db.String(15), unique=True, nullable=False)
    nacionalidad = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    es_sysadmin = db.Column(db.Boolean, nullable=False)

    # Campo para indicar si el usuario está bloqueado
    is_locked = db.Column(db.Boolean, default=False, nullable=False)

    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    rol = db.relationship("Rol", back_populates="usuarios")

    tarjeta = db.relationship("Tarjeta", back_populates="usuario", uselist=False)

    def es_mayor_de_edad(self):
        today = date.today()
        edad = today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
        return edad >= 18

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def bloquear(self):
        self.is_locked = True

    def desbloquear(self):
        self.is_locked = False

    
    def tiene_permiso(self, nombre_permiso):
        """
        Returna True/False dependiendo de si el Rol del usuario está asociado al permiso con el nombre dado. Si el usuario no tiene un rol asignado, retorna False.
        Si no existe un permiso con ese nombre, lanza una excepción (útil para no equivocarse de nombre al crear nuestro código)
        """
        if self.es_sysadmin:
            if not Permiso.query.filter_by(nombre=nombre_permiso).first():
                raise Exception(f"El permiso {nombre_permiso} no existe")
            return True
        if self.rol is None:
            return False
        return self.rol.tiene_permiso(nombre_permiso)
    
    def __repr__(self):
        return f'<User {self.username}>'
