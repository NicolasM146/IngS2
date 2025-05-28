from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from src.core.Usuario.User import User

class PropertyForm(FlaskForm):
    direccion = StringField('Dirección', validators=[DataRequired()])
    localidad = StringField('Localidad', validators=[DataRequired()])
    capacidad = IntegerField('Capacidad', validators=[DataRequired()])
    habitaciones = IntegerField('Habitaciones', validators=[DataRequired()])
    estado = SelectField('Estado', choices=[
        ('disponible', 'Disponible'), 
        ('ocupado', 'Ocupado')
    ], validators=[DataRequired()])
    descripcion = TextAreaField('Descripción')
    usuario_id = SelectField(
        'Propietario',
        coerce=int,
        choices=[],
        validators=[DataRequired()],
        description="Seleccione el dueño del inmueble"
    )
    
    def __init__(self, *args, **kwargs):
        super(PropertyForm, self).__init__(*args, **kwargs)
        # Carga usuarios activos no bloqueados y con email confirmado
        self.usuario_id.choices = [
            (user.id, f"{user.nombre} (DNI: {user.dni}) - Tel: {user.telefono}") 
            for user in User.query.filter_by(
                is_locked=False,
                email_confirmed=True
            ).order_by(User.nombre).all()
        ]