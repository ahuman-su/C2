from flask import request, jsonify, Blueprint
from app.jwt_handler import validate_token

check = Blueprint('check-token', __name__)

@check.route('/check-token', methods=['GET'])
def check_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"valid": False}), 402

    token = auth_header.split(" ")[1]

    result = validate_token(token)
    if result["success"]:
        return jsonify({"valid": True})

    return jsonify({"valid": False, "error": result["message"]}), result["status"]
