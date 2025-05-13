import os
from flask import Flask, render_template
from src.core.database import db
from src.web.config import Config
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def create_app(env="development"):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_folder = os.path.join(base_dir, "templates")
    static_folder = os.path.abspath(os.path.join(base_dir, "../../../static"))  # si la carpeta existe afuera

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    
    from . import commands
    commands.register(app)
    @app.route('/')
    def home():
        return render_template("home.html")
    
    print("Template folder cargado:", app.template_folder)
    return app
