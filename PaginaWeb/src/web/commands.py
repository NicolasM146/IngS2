from src.core import database as db


def register(app):
    @app.cli.command(name="reset-db")
    def reset_db():
        db.reset()

    @app.cli.command(name="populate-db")
    def seed_db():
        db.reset()
        seeds.run()

