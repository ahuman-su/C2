import jwt
from flask import Blueprint, jsonify, request

from app.jwt_handler import SECRET_KEY, verify_token
from DB import get_db_connection

check = Blueprint("check-token", __name__)


@check.route("/check-token", methods=["GET"])
def check_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"valid": False}), 402

    token = auth_header.split(" ")[1]

    try:
        result = verify_token(token)
        # Convertir le résultat jsonify en dictionnaire
        result_dict = result.get_json() if hasattr(result, "get_json") else result
        if result_dict.get("success"):
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded.get("user_id")

            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT id
                    FROM utilisateurs
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                exists = cursor.fetchone()
            finally:
                conn.close()

            if exists is None:
                return jsonify({"valid": False, "error": "user_not_found"}), 401
            return jsonify({"valid": True})
        else:
            return jsonify({"valid": False, "error": result_dict.get("error")}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "invalid"}), 401
