import jwt
import datetime
import os
from dotenv import load_dotenv
from flask import jsonify, request, g
from functools import wraps
from DB import get_db_connection


#chargé les variables de configuration depuis le fichier .env'
load_dotenv()

# Accès aux variables
SECRET_KEY = os.getenv("SECRET_KEY", "clé-si-pas-la")

def local_now():
    return datetime.datetime.now()


def serialize_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    return str(value)


def normalize_datetime(value):
    if value is None or isinstance(value, datetime.datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.datetime.fromisoformat(value.strip().replace("Z", "")) #parce que quand on demande le date time il rajout un Z aprés
        except ValueError:
            return None

    return None


def get_user_from_db(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id, email, username, is_admin, is_blocked, is_invited, expiration_date
            FROM utilisateurs
            WHERE id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "email": row["email"],
        "username": row["username"],
        "is_admin": bool(row["is_admin"]),
        "is_blocked": bool(row["is_blocked"]),
        "is_invited": bool(row["is_invited"]),
        "expiration_date": normalize_datetime(row["expiration_date"]),
    }


def get_account_access_error(user):
    if user["is_blocked"]:
        return "Compte bloque"

    expiration_date = user["expiration_date"]
    if expiration_date is not None and expiration_date <= local_now():
        return "Compte expire"

    return None


def generate_token(user_id):
    return jwt.encode({"user_id": user_id}, SECRET_KEY, algorithm="HS256")

def validate_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return {"success": False, "message": "Token invalide", "status": 401}

    user_id = decoded.get("user_id")
    user = get_user_from_db(user_id)
    if user is None:
        return {"success": False, "message": "Compte introuvable", "status": 401}

    access_error = get_account_access_error(user)
    if access_error:
        return {"success": False, "message": access_error, "status": 403}

    return {
        "success": True,
        "user_id": user_id,
        "user": user,
        "status": 200,
    }


def verify_token(token):
    result = validate_token(token)
    if result["success"]:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": result["message"]})



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token manquant'}), 401

        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]

            result = validate_token(token)
            if not result["success"]:
                return jsonify({'message': result["message"]}), result["status"]

            g.user_data = {"user_id": result["user_id"]}
            g.current_user = result["user"]
        except Exception as exc:
            return jsonify({'message': f'Erreur authentification: {exc}'}), 500

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.current_user.get("is_admin"):
            return jsonify({'message': 'Acces reserve aux administrateurs'}), 403
        return f(*args, **kwargs)

    return token_required(decorated)
