import os

class Config:
    # If SECRET_KEY is not set, create_app() generates one and stores it in instance/secret_key.
    SECRET_KEY = os.getenv("SECRET_KEY") or None
    # Shared password for the login page. The app cannot be used until it is set.
    APP_PASSWORD = os.getenv("APP_PASSWORD") or None
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dentist.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEFAULT_APPOINTMENT_MINUTES = int(os.getenv("DEFAULT_APPOINTMENT_MINUTES", "30"))
