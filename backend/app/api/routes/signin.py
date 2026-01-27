from flask import Blueprint, request, jsonify
import bcrypt
from sqlalchemy import select

from DB import get_db_session
from DB.models import Utilisateur
from app.jwt_handler import generate_token
signin_bp = Blueprint('signin', __name__)

@signin_bp.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()

    email = data['email']
    password = data['password']

    with get_db_session() as session:
        stmt = select(Utilisateur).where(Utilisateur.email == email)
        user = session.execute(stmt).scalar_one_or_none()

    if user is None:
        return jsonify({"success": False})

    data = {"id": user.id, "email": user.email, "password": user.password}

    check = bcrypt.checkpw(
        password=password.encode('utf-8'),
        hashed_password=data['password']
    )

    if check:
        token = generate_token(user_id=data['id'])
        return jsonify({"success": True, "token": token})

    return jsonify({"success": False})
