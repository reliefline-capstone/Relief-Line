import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "mysql+pymysql://root:@localhost/reliefline_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # The whole system runs on Philippine time. Pin every DB connection's
    # session time zone to UTC+8 so MySQL-side CURRENT_TIMESTAMP / NOW()
    # server defaults match the Python-side ph_now() writes, regardless of
    # what time zone the host container happens to be set to (Codespaces
    # runs UTC, a local machine may run PH — this makes both behave the same).
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"init_command": "SET time_zone = '+08:00'"},
    }