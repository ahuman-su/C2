from flask import Blueprint, request, jsonify
import bcrypt
from sqlalchemy.exc import IntegrityError

from DB import get_db_session
from DB.models import Utilisateur
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

    try:
        with get_db_session() as session:
            user = Utilisateur(
                prenom=prenom,
                nom=nom,
                username=username,
                email=email,
                password=hash_password,
                ville=ville,
            )
            session.add(user)
            session.flush()
            token = generate_token(user_id=user.id)
    except IntegrityError:
        return jsonify({"success": False, "error": "email_deja_utilise"}), 409

    return jsonify({"success": True, "token": token})
