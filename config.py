import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    MAX_BULLYING_COUNT = int(os.getenv('MAX_BULLYING_COUNT'))
    
    # SQLAlchemy pool settings to prevent lock timeouts
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connections before using
        'pool_recycle': 300,    # Recycle connections after 5 minutes
        'pool_size': 10,        # Number of connections to maintain
        'max_overflow': 20,     # Max additional connections
        'pool_timeout': 30,     # Timeout for getting connection from pool
    }

