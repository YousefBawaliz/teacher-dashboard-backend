"""
Configuration settings for the Teacher Dashboard application.
"""
import os
from datetime import timedelta

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', '111')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_TITLE = "Teacher Dashboard API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    # Session config
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # CORS settings
    CORS_SUPPORTS_CREDENTIALS = True


class DevConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///teacher_dashboard_dev.db')
    SESSION_COOKIE_SECURE = False  # Allow non-HTTPS in development


class TestConfig(Config):
    """Test configuration."""
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_PROTECTION = 'strong'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


class ProdConfig(Config):
    """Production configuration."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///teacher_dashboard_prod.db')
    DEBUG = False
    # In production, ensure proper secret key is set
    SECRET_KEY = os.environ.get('SECRET_KEY', '111')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production application")
