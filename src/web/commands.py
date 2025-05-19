from flask.cli import with_appcontext
from src.core import database as db


def register(app):
    @app.cli.command("reset-db")
    @with_appcontext
    def reset_db():
        db.reset()
