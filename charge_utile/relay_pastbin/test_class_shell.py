import requests
import os
import time
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

dotenv_path = os.path.join(os.path.dirname(__file__), "../..", "backend", ".env")
load_dotenv(dotenv_path)
API_KEY = os.getenv("API_KEY", "clé-si-pas-la")
USER = os.getenv("USER_PAST", "user")
PASSWORD = os.getenv("PASSWORD", "password")
num_commande = 1
commande = "ls"

print(API_KEY, USER, PASSWORD)
find = False

def generate_user_key(API_KEY, USER, PASSWORD):
    r = requests.post("https://pastebin.com/api/api_login.php", data={
        "api_dev_key": API_KEY,
        "api_user_name": USER,
        "api_user_password": PASSWORD
    })
    r.raise_for_status()
    api_user_key = r.text.strip()
    return api_user_key

# 1) Login -> api_user_key
api_user_key = generate_user_key(API_KEY, USER, PASSWORD)
#2) crée le paste

paste_url = "https://pastebin.com/api/api_post.php"

data = {
    "api_dev_key": API_KEY,
    "api_user_key": api_user_key,
    "api_option": "paste",
    "api_paste_code": commande,               #Texte
    "api_paste_name": "commade_" + str(num_commande),# Titre
    "api_paste_private": "2",                 # 0=public, 1=unlisted, 2=private
    "api_paste_expire_date": "N"              # "N" = jamais, "10M"=10 minutes, "1H"=1 heure, etc.
}

response = requests.post(paste_url, data=data)
print("URL du paste:", response.text)


#recupére les dernier reponse et verifie que c'est le bon'
while not find:
    #refaire la user_key
    api_user_key = generate_user_key(API_KEY, USER, PASSWORD)

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


        if nom_past != "Sans titre" and nom_past.find("_reponse") != -1:
            find = True
        else:
            print("pas trouvé")

    print("no paste find")
    time.sleep(10)

print(f"Dernier paste: key={paste_key}, title={nom_past}, ts={latest_ts}")

api_user_key = generate_user_key(API_KEY, USER, PASSWORD)
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
