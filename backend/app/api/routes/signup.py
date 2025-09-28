from flask import Blueprint, request, jsonify
import bcrypt
from DB import get_db_connection
from app.jwt_handler import generate_token

signup_bp = Blueprint('signup', __name__)

@signup_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    prenom = data['prenom']
    nom = data['nom']
    username = data['username']
    email = data['email']
    password = data['password']
    ville = data['ville']

    hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
                   INSERT INTO utilisateurs (prenom, nom, username, email, password, ville)
                   VALUES (?, ?, ?, ?, ?, ?)
                   """, (prenom, nom, username, email, hash_password, ville))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "token": generate_token(user_id=1)})
