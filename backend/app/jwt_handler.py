import datetime
import os
from functools import wraps

import jwt
from dotenv import load_dotenv
from flask import g, jsonify, request

from DB import get_db_connection


#chargé les variables de configuration depuis le fichier .env'
load_dotenv()

# Accès aux variables
SECRET_KEY = os.getenv("SECRET_KEY", "clé-si-pas-la")
JWT_EXPIRATION_DELTA = int(os.getenv("JWT_EXPIRATION_DELTA", 86400))


def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION_DELTA),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"success": True})
    except jwt.ExpiredSignatureError:
        return {"error": "Token expiré"}
    except jwt.InvalidTokenError:
        return {"error": "Token invalide"}



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": "Token manquant"}), 401

        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]

            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT id
                    FROM utilisateurs
                    WHERE id = %s
                    """,
                    (decoded.get("user_id"),),
                )
                exists = cursor.fetchone()
            finally:
                conn.close()

            if exists is None:
                return jsonify({"message": "Utilisateur introuvable"}), 401
            g.user_data = decoded  # Stocke les données du token dans le contexte Flask
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expiré"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token invalide"}), 401

        return f(*args, **kwargs)

    return decorated
