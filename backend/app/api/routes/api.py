from flask import Blueprint

# Déclarer un blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/test', methods=['GET'])
def test_route():
    return {"message": "This is a test route!"}