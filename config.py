import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dentist.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEFAULT_APPOINTMENT_MINUTES = int(os.getenv("DEFAULT_APPOINTMENT_MINUTES", "30"))
