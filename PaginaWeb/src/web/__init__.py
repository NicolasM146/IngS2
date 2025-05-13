from flask import Flask
from flask import render_template
from src.core.database import db
from src.core.bcrypt import bcrypt

def create_app(env="development", static_folder="../static", template_folder="../templates"):
    app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)


    # Inicializar la base de datos con la app
    db.init_app(app)
    bcrypt.init_app(app)
    
    @app.route('/')
    def home():
        return render_template("home.html")

    return app
