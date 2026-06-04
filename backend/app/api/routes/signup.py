from flask import Blueprint, request, jsonify
import bcrypt
import datetime
import pymysql
from DB import get_db_connection
from app.jwt_handler import generate_token
from app.jwt_handler import local_now

signup_bp = Blueprint('signup', __name__)

def get_expiration_date(hours):
    if not hours:
        return None

    try:
        hours = int(hours)
    except (TypeError, ValueError):
        raise ValueError("Duree invalide. Entre un nombre d'heures, exemple: 2.")

    if hours <= 0:
        raise ValueError("La duree doit etre superieure a zero.")
    return local_now() + datetime.timedelta(hours=hours)


@signup_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}

    required_fields = ("prenom", "nom", "username", "email", "password")
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({
            "success": False,
            "message": "Champs requis manquants: " + ", ".join(missing_fields),
        }), 400

    prenom = data['prenom']
    nom = data['nom']
    username = data['username']
    email = data['email']
    password = data['password']

    try:
        expiration_date = get_expiration_date(data.get("expiration_hours"))
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400

    is_invited = expiration_date is not None

    hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                       INSERT INTO utilisateurs (
                           prenom,
                           nom,
                           username,
                           email,
                           password,
                           is_invited,
                           expiration_date
                       )
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       """, (
                           prenom,
                           nom,
                           username,
                           email,
                           hash_password,
                           is_invited,
                           expiration_date,
                       ))

        conn.commit()
        user_id = cursor.lastrowid
    except pymysql.err.IntegrityError:
        conn.rollback()
        return jsonify({"success": False, "message": "Email deja utilise."}), 409
    finally:
        conn.close()

    return jsonify({"success": True, "token": generate_token(user_id=user_id)})
