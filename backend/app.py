# backend/app.py
from app import create_app
from flask import Flask
import secrets


app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = secrets.token_hex(4096)
app = create_app()  # Crée et configure l'application Flask avec CORS

if __name__ == '__main__':
    # Démarrer le serveur Flask
    app.run(debug=True)