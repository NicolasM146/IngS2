from flask import Flask
from flask import render_template
from src.core.database import db

def create_app(env="development", static_folder="../static", template_folder="../templates"):
    app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)

    # Configurar la URI de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'  # O la que uses
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar la base de datos con la app
    db.init_app(app)

    @app.route('/')
    def home():
        return render_template("home.html")

    return app
