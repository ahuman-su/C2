from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Importez et enregistrez les blueprints ici
    from .api.routes.api import api_bp
    from .api.routes.signup import signup_bp
    from .api.routes.signin import signin_bp
    from .api.routes.check_request import check
    from .api.routes.dashboard.terminal import (
        terminal,
        listener,
        shells_list_bp,
        supprimer_shell_bp,
    )
    from .api.routes.dashboard.meteo import meteo

    app.register_blueprint(api_bp, url_prefix='/api')      # Route de l'API
    app.register_blueprint(signup_bp, url_prefix='/auth')  # Route pour signup
    app.register_blueprint(signin_bp, url_prefix='/auth')
    app.register_blueprint(check, url_prefix='/api')
    app.register_blueprint(terminal, url_prefix='/dashboard')
    app.register_blueprint(listener, url_prefix='/dashboard')
    app.register_blueprint(shells_list_bp, url_prefix='/dashboard')
    app.register_blueprint(supprimer_shell_bp, url_prefix='/dashboard')
    app.register_blueprint(meteo, url_prefix='/dashboard')
    print("✅ Blueprints enregistrés avec succès !")


    return app
