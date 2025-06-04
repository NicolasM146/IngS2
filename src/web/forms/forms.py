from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from src.core.Usuario.User import User
from wtforms.validators import Optional, NumberRange
from flask_wtf.file import FileField, FileRequired, FileAllowed

# Formualrio para registrar o actualizar un Inmueble
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
        'Encargado',
        coerce=int,
        choices=[],
        validators=[DataRequired()],
        description="Seleccione el dueño del inmueble"
    )
    #Formulario para subir fotos de un Inmueble   
    
    photos = FileField('Fotos de la propiedad', validators=[
        FileRequired(message='Debe cargar al menos una foto'),
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Solo imágenes (jpg, png, jpeg, gif)')
    ], render_kw={"multiple": True})

 
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



# Formulario para filtrar en la Busqueda de Inmuebles
class PropertySearchForm(FlaskForm):
    # Campos de texto
    direccion = StringField('Dirección', validators=[Optional()], 
                          render_kw={"placeholder": "Ej: Calle Principal 123"})
    
    localidad = StringField('Localidad', validators=[Optional()],
                          render_kw={"placeholder": "Ej: Buenos Aires"})
    
    # Campos de selección
    estado = SelectField('Estado', choices=[
        ('', 'Todos los estados'),
        ('disponible', 'Disponible'),
        ('ocupado', 'Ocupado'),
        ('dado_de_baja', 'Dado de baja'),
    ], validators=[Optional()])
    
    capacidad = SelectField('Capacidad', choices=[
        ('', 'Cualquier capacidad'),
        ('1', '1 persona'),
        ('2', '2 personas'),
        ('4', '4 personas'),
        ('6', '6 personas'),
        ('8', '8 personas')
    ], validators=[Optional()])
    
    habitaciones = SelectField('Habitaciones', choices=[
        ('', 'Cualquier cantidad'),
        ('1', '1 habitacion'),
        ('2', '2 habitaciones'),
        ('3', '3 habitaciones'),
        ('4', '4 habitaciones'),
        ('5', '5 habitaciones')
    ], validators=[Optional()])
    
    publicado = SelectField(
        'Alquiler',
        choices=[
            ('', '---'),
            ('si', 'Publicado para alquilar'),
            ('no', 'Sin publicar para alquilar')
        ]
    )
    
    buscar = SubmitField('Buscar', render_kw={"class": "btn btn-primary"})