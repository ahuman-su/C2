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
        machine_info_bp,
    )
    from .api.routes.dashboard.hibp import hibp
    from .api.routes.dashboard.storage import storage_bp
    from .api.routes.dashboard.admin import admin_bp
    from .db_schema import ensure_dashboard_tables
    from .account_cleanup import delete_expired_accounts_if_due

    try:
        ensure_dashboard_tables()
    except Exception as exc:
        print(f"⚠️ Initialisation differree du schema dashboard: {exc}")

    try:
        deleted_accounts = delete_expired_accounts_if_due(force=True)
        if deleted_accounts:
            print(f"Comptes expires supprimes: {deleted_accounts}")
    except Exception as exc:
        print(f"Nettoyage initial des comptes expires impossible: {exc}")

    @app.before_request
    def cleanup_expired_accounts_before_request():
        try:
            deleted_accounts = delete_expired_accounts_if_due()
            if deleted_accounts:
                print(f"Comptes expires supprimes: {deleted_accounts}")
        except Exception as exc:
            print(f"Nettoyage des comptes expires impossible: {exc}")

    app.register_blueprint(api_bp, url_prefix='/api')      # Route de l'API
    app.register_blueprint(signup_bp, url_prefix='/auth')  # Route pour signup
    app.register_blueprint(signin_bp, url_prefix='/auth')
    app.register_blueprint(check, url_prefix='/api')
    app.register_blueprint(terminal, url_prefix='/dashboard')
    app.register_blueprint(listener, url_prefix='/dashboard')
    app.register_blueprint(shells_list_bp, url_prefix='/dashboard')
    app.register_blueprint(supprimer_shell_bp, url_prefix='/dashboard')
    app.register_blueprint(machine_info_bp, url_prefix='/dashboard')
    app.register_blueprint(hibp, url_prefix='/dashboard')
    app.register_blueprint(storage_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/dashboard')
    print("✅ Blueprints enregistrés avec succès !")


    return app
