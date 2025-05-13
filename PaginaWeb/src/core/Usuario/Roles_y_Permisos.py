from src.core.database import db
from sqlalchemy import event
from sqlalchemy.orm import Session

roles_permisos = db.Table(
    "roles_permisos",
    db.Column("rol_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permiso_id", db.Integer, db.ForeignKey("permisos.id"), primary_key=True),
)


class Rol(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), unique=True, nullable=False)

    usuarios = db.relationship("User", back_populates="rol")
    permisos = db.relationship("Permiso", secondary=roles_permisos)

    def __repr__(self):
        return f'<Rol #{self.id} = "{self.nombre}">'

    def tiene_permiso(self, nombre_permiso):
        """
        Returna True/False dependiendo de si el Rol está asociado al permiso con el nombre dado.
        Si no existe un permiso con ese nombre, lanza una excepción (útil para no equivocarse de nombre al crear nuestro código)
        """
        if not Permiso.query.filter_by(nombre=nombre_permiso).first():
            raise Exception(f"El permiso {nombre_permiso} no existe")
        return any(permiso.nombre == nombre_permiso for permiso in self.permisos)


class Permiso(db.Model):
    __tablename__ = "permisos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return f'<Permiso #{self.id} = "{self.nombre}">'


def crear_rol(_tabla, sesion: Session, nombre):
    """
    Función interna para crear los roles iniciales.
    """
    rol = Rol(nombre=nombre)
    sesion.add(rol)
    sesion.commit()
    return rol


def crear_y_asignar_permisos(sesion: Session, permisos):
    """
    Función interna para asignar los permisos a los roles asociados.
    """
    for nombre, roles in permisos.items():
        permiso = Permiso(nombre=nombre)
        sesion.add(permiso)
        for rol in roles:
            rol.permisos.append(permiso)
        sesion.commit()


@event.listens_for(roles_permisos, "after_create")
def crear_roles_y_permisos(tabla, coneccion, **kw):
    """
    Esto correrá al hacer reset-db.
    Crea los roles por defecto y les asigna todos los permisos.
    """
    with Session(coneccion) as sesion:
        check_in_out = crear_rol(tabla, sesion, "CheckInOut") 
        client = crear_rol(tabla, sesion, "client") 
        # Al crear nuevos permisos, agréguenlos a la lista
        # (siempre dejen una coma en el último item, así hay menos posibilidades de errores al mergear)
        crear_y_asignar_permisos(
            sesion,
            {
                "user_index": [],
                "user_show": [],
                "user_update": [],
                "user_create": [],
                "user_destroy": [],
                
                "properties_index": [],
                "properties_show": [],
                "properties_update": [],
                "properties_create": [],
                "properties_destroy": [],
                
                "rentals_index": [],
                "rentals_show": [],
                "rentals_update": [],
                "rentals_create": [],
                "rentals_destroy": [],
                
                "properties_check_in": [check_in_out],  # Asignando permisos específicos al rol
                "properties_check_out": [check_in_out],  # Lo mismo aquí
            },
        )

        print("Permisos para cada rol:")
        for rol in sesion.query(Rol).all():
            print(f"- {rol.nombre}: {[permiso.nombre for permiso in rol.permisos]}")