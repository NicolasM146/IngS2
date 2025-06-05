from src.web.controllers.user import bp as User_bp  # Importar el Blueprint
from src.web.controllers.Register import bp as Register_bp  # Importar el Blueprint
from src.web.controllers.login import bp as Login_bp  # Importar el Blueprint
from src.web.controllers.property import bp as Property_bp
from src.web.controllers.rental import bp as Rental_bp  # Importar el Blueprint de alquileres
from src.web.controllers.Reservation import bp as reservation_bp
from flask import render_template
from flask import render_template, redirect, url_for
from flask_login import current_user

def register(app):
    @app.route("/")
    def home():
        if not current_user.is_authenticated:
        
          return redirect(url_for("login.login"))  # Cambiá "login.login" según el nombre de tu blueprint y ruta login
        return render_template("home.html")


    app.register_blueprint(User_bp)  # Registrar el Blueprint de los usuarios
    app.register_blueprint(Register_bp)  # Registrar el Blueprint de los usuarios con un prefijo
    app.register_blueprint(Login_bp)  # Registrar el Blueprint de los usuarios con un prefijo
    app.register_blueprint(Property_bp) # Registrar el Blueprint de los inmuebles con un prefijo
    app.register_blueprint(Rental_bp)  # Registrar el Blueprint de los alquileres con un prefijo
    app.register_blueprint(reservation_bp)