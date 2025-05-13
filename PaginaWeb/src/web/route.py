from src.web.controllers.user import bp as User_bp  # Importar el Blueprint
from flask import render_template

def register(app):
    @app.route("/")
    def home():
        return render_template("home.html")

    app.register_blueprint(User_bp)  # Registrar el Blueprint de los usuarios
