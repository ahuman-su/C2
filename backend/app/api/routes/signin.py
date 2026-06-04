from flask import Blueprint, request, jsonify
import bcrypt
from DB import get_db_connection
from app.jwt_handler import generate_token
from app.jwt_handler import get_account_access_error
from app.jwt_handler import normalize_datetime
signin_bp = Blueprint('signin', __name__)

@signin_bp.route('/signin', methods=['POST'])
def signin():
    data = request.get_json() or {}

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"success": False, "message": "Email et mot de passe requis."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                       SELECT
                           id,
                           email,
                           username,
                           password,
                           is_admin,
                           is_blocked,
                           is_invited,
                           expiration_date
                       FROM utilisateurs
                       WHERE email = (%s)
                           """, (email,))
        rows = cursor.fetchone()
    finally:
        conn.close()

    if rows is None:
        return jsonify({"success": False})

    check = bcrypt.checkpw(
        password=password.encode('utf-8'),
        hashed_password=rows['password']
    )

    if check:
        user = {
            "id": rows["id"],
            "email": rows["email"],
            "username": rows["username"],
            "is_admin": bool(rows["is_admin"]),
            "is_blocked": bool(rows["is_blocked"]),
            "is_invited": bool(rows["is_invited"]),
            "expiration_date": normalize_datetime(rows["expiration_date"]),
        }
        access_error = get_account_access_error(user)
        if access_error:
            return jsonify({"success": False, "message": access_error}), 403

        token = generate_token(user_id=rows['id'])
        return jsonify({"success": True, "token": token})

    return jsonify({"success": False})
