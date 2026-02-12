import bcrypt
from flask import Blueprint, jsonify, request

from DB import get_db_connection
from app.jwt_handler import generate_token

signin_bp = Blueprint("signin", __name__)


@signin_bp.route("/signin", methods=["POST"])
def signin():
    data = request.get_json()

    email = data["email"]
    password = data["password"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, email, password
            FROM utilisateurs
            WHERE email = %s
            """,
            (email,),
        )
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"success": False})

    check = bcrypt.checkpw(
        password=password.encode("utf-8"),
        hashed_password=row["password"],
    )

    if check:
        token = generate_token(user_id=row["id"])
        return jsonify({"success": True, "token": token})

    return jsonify({"success": False})
