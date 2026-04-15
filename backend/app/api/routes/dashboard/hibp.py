import hashlib

import requests
from flask import Blueprint, jsonify, request

from app.jwt_handler import token_required

HIBP_HEADERS = {
    "User-Agent": "C2Control/1.0",
    "Add-Padding": "true",
}

hibp = Blueprint("hibp", __name__)


def lookup_password_exposure(password):
    password_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix = password_hash[:5]
    suffix = password_hash[5:]

    response = requests.get(
        f"https://api.pwnedpasswords.com/range/{prefix}",
        headers=HIBP_HEADERS,
        timeout=10,
    )
    response.raise_for_status()

    for line in response.text.splitlines():
        hash_suffix, _, count = line.partition(":")
        if hash_suffix == suffix:
            try:
                return int(count.strip())
            except ValueError:
                return 0

    return 0


@hibp.route("/pwned-password", methods=["POST"])
@token_required
def check_pwned_password():
    payload = request.get_json(silent=True) or {}
    password = payload.get("password")

    if not isinstance(password, str) or password == "":
        return jsonify({"message": "Mot de passe requis."}), 400

    try:
        count = lookup_password_exposure(password)
    except requests.RequestException:
        return jsonify({"message": "Service Have I Been Pwned indisponible."}), 503

    exposed = count > 0
    message = (
        f"Ce mot de passe apparait {count} fois dans des fuites connues."
        if exposed
        else "Aucune fuite connue pour ce mot de passe."
    )

    return (
        jsonify(
            {
                "count": count,
                "exposed": exposed,
                "message": message,
                "severity": "danger" if exposed else "safe",
            }
        ),
        200,
    )
