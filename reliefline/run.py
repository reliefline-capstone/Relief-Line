# Starts the app on your computer for development (python run.py).

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
