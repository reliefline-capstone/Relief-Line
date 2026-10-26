# Starts the app on the server (the hosting site's WSGI setup loads 'app' from here).

from app import create_app

app = create_app()
