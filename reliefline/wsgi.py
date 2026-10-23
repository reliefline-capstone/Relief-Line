# Starts the app on the server (used by gunicorn / waitress, see Procfile).

from app import create_app

app = create_app()
