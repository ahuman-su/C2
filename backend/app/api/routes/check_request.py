from flask import request, jsonify, Blueprint
import jwt
from app.jwt_handler import verify_token

check = Blueprint('check-token', __name__)

@check.route('/check-token', methods=['GET'])
def check_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"valid": False}), 402

    token = auth_header.split(" ")[1]

    try:
        result = verify_token(token)
        # Convertir le résultat jsonify en dictionnaire
        result_dict = result.get_json()
        if result_dict.get("success"):
            return jsonify({"valid": True})
        else:
            return jsonify({"valid": False, "error": result_dict.get("error")}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "invalid"}), 401
