import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32)
    
    # Session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'
    
    # Database configuration - prioritize NEON_CONNECTION_STRING
    SQLALCHEMY_DATABASE_URI = os.environ.get("NEON_CONNECTION_STRING") or os.environ.get("DATABASE_URL") or "postgresql://neondb_owner:npg_3uxsWqBoh5HY@ep-aged-poetry-aix5dc0j-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Email configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    
    # Application settings
    MIN_DELIVERY_FEE = 40  # EGP
    MAX_DELIVERY_FEE = 80  # EGP
    ADVANCE_PAYMENT_PERCENTAGE = 20  # 20% advance payment
