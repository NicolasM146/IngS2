import os
from flask import Flask, render_template
from src.core.database import db
from src.web.config import Config
from src.core.bcrypt import bcrypt
from src.web import route
from flask_mail import Mail

mail = Mail()

def create_app(env="development"):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_folder = os.path.join(base_dir, "templates")
    static_folder = os.path.abspath(os.path.join(base_dir, "../../../static"))  # si la carpeta existe afuera

    
    
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.config.from_object(Config)
    
        
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'tu_correo@gmail.com'
    app.config['MAIL_PASSWORD'] = 'jugm embt cqqf gxpx'  # usa contraseña de aplicación de Google

    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    
    from . import commands
    commands.register(app)
    route.register(app)

    

    print("Template folder cargado:", app.template_folder)
    return app
