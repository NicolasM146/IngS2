import os
from dotenv import load_dotenv

# Carga las variables de entorno del archivo .env en la raíz del proyecto
load_dotenv()

class Config(object):
    """Base configuration."""

    SECRET_KEY = "secret"
    TESTING = False
    SESSION_TYPE = "filesystem"
    
    # Configuración de Stripe usando variables del .env
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

    # Datos de la base de datos para todos los entornos
    DB_USER = "postgres"
    DB_PASSWORD = "postgres"
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "Ing2"
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 60,
        "pool_pre_ping": True,
    }
    
    print(SQLALCHEMY_DATABASE_URI)


config = Config()
