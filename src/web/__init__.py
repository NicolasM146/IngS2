import os
from flask import Flask
from flask_mail import Mail
from flask_login import LoginManager
from src.core.database import db, init_app
from src.web.config import Config
from src.core.bcrypt import bcrypt
from src.web import route
from src.core.Usuario.User import User

mail = Mail()
login_manager = LoginManager()

def create_app(env="development"):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_folder = os.path.join(base_dir, "templates")
    static_folder = os.path.abspath(os.path.join(base_dir, "../../static"))

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.config.from_object(Config)

    # Configuración de correo
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'alquiloandoad@gmail.com'
    app.config['MAIL_PASSWORD'] = 'teqx ukpl zykq axzh'
    app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

    # Inicializar extensiones
    init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "login.login"
    login_manager.login_message = "Debes iniciar sesión para acceder a esta página"

    from . import commands
    commands.register(app)
    route.register(app)

    import stripe
    stripe.api_key = app.config["STRIPE_SECRET_KEY"]

    print("Template folder cargado:", app.template_folder)

    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
