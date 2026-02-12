import bcrypt
import pymysql
from flask import Blueprint, jsonify, request

from DB import get_db_connection
from app.jwt_handler import generate_token

signup_bp = Blueprint("signup", __name__)


@signup_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    prenom = data["prenom"]
    nom = data["nom"]
    username = data["username"]
    email = data["email"]
    password = data["password"]
    ville = data["ville"]

    hash_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO utilisateurs (prenom, nom, username, email, password, ville)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (prenom, nom, username, email, hash_password, ville),
        )
        conn.commit()
        token = generate_token(user_id=cursor.lastrowid)
    except pymysql.err.IntegrityError:
        conn.rollback()
        return jsonify({"success": False, "error": "email_deja_utilise"}), 409
    finally:
        conn.close()

    return jsonify({"success": True, "token": token})
