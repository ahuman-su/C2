from flask import request, jsonify, Blueprint, g
import jwt
from app.jwt_handler import verify_token, token_required
from DB import get_db_connection
import requests

HEADERS = {
    "User-Agent": "C2Control/1.0 (contact@example.com)",
}




meteo = Blueprint('meteo', __name__)


@meteo.route('/meteo', methods=['GET'])
@token_required
def meteo_ville():
    user_info = g.user_data  # Données décodées du token
    user_id = user_info["user_id"]
    return jsonify({"message":  ville(user_id), "user": user_id}), 200



def ville(id_user):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT ville 
                   FROM utilisateurs 
                   WHERE id = (?)
                       """, (id_user,))
    rows = cursor.fetchone()
    if rows is None:
        return "Ville non trouvé"

    VILLE = rows[0]
    print(VILLE, "*******************************************")
    conn.close()
    # Pour transformer le nom de ville en coordonnées, on peut utiliser Nominatim (OpenStreetMap)
    geo_url = f"https://nominatim.openstreetmap.org/search?city={VILLE}&format=json"
    try:
        geo_resp = requests.get(geo_url, headers=HEADERS, timeout=5)
        geo_resp.raise_for_status()
        geo = geo_resp.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"Erreur lors de la requete geocodage: {exc}")
        return "Service meteo indisponible"

    if geo:
        lat = geo[0]["lat"]
        lon = geo[0]["lon"]

        meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        try:
            meteo_resp = requests.get(meteo_url, headers=HEADERS, timeout=5)
            meteo_resp.raise_for_status()
            data = meteo_resp.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"Erreur lors de la requete meteo: {exc}")
            return "Service meteo indisponible"

        current = data.get("current_weather") or {}
        temp = current.get("temperature")
        wind = current.get("windspeed")

        if temp is None or wind is None:
            return "Donnees meteo indisponibles"

        return (f"Meteo a {VILLE} : {temp}°C, vent {wind} km/h")
    else:
        return ("Ville introuvable")




