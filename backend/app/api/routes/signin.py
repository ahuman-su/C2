from flask import Blueprint, request, jsonify
import bcrypt
from backend.DB import get_db_connection
from backend.app.jwt_handler import generate_token
signin_bp = Blueprint('signin', __name__)

@signin_bp.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()

    email = data['email']
    password = data['password']

    hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT id, email, password 
                   FROM utilisateurs 
                   WHERE email = (?)
                       """, (email,))
    rows = cursor.fetchone()

    if rows is None:
        return jsonify({"success": False})

    # Convert Row objects to dictionaries
    data = {"id": rows[0], "email": rows[1], "password": rows[2]}

    check = bcrypt.checkpw(
        password=password.encode('utf-8'),
        hashed_password=data['password']
    )

    if check:
        token = generate_token(user_id=data['id'])
        return jsonify({"success": True, "token": token})

    return jsonify({"success": False})