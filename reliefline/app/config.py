# App settings, read from the .env file.

import os
from dotenv import load_dotenv

load_dotenv()


# Reads an on/off setting from the .env file.
# '1', 'true', 'yes' or 'on' mean ON; anything else means OFF.
def _env_flag(name, default="false"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# All app settings in one place: database, security key, debug mode, upload size limit and login cookies.
# Values come from the .env file (on your computer and on the server).
class Config:
    DEBUG = _env_flag("FLASK_DEBUG")

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost/reliefline_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"init_command": "SET time_zone = '+08:00'"},
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "32")) * 1024 * 1024

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_flag("SESSION_COOKIE_SECURE")
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    BEHIND_PROXY = _env_flag("BEHIND_PROXY")
