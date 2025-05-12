from flask import Flask
from flask import render_template
def create_app(env="development", static_folder="../static", template_folder="../templates"):
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return render_template("home.html")
    
    return app
