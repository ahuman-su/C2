import requests
import subprocess
from datetime import datetime

class forum:
    def __init__(self, ip, port, user, password):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.find = False
        self.num_commande = 1

    def generate_user_key(self):
        response = requests.post(
            f"http://{self.ip}:{self.port}/api/auth/login",
            json={"username": self.user, "password": self.password},
        )
        response.raise_for_status()

        token = response.json()["token"]
        return token

    def execute(self,commande):
        self.find = False
        #genere le token
        token = self.generate_user_key()

        #envoie la commande
        response = requests.post(
            f"http://{self.ip}:{self.port}/api/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"body": commande},
        )

        #attendre la repones et récupérer la dernier
        last = {'body': 'vide', 'createdAt': '2000-01-22T17:15:13.611397', 'id': 0, 'username': 'C2'}
        while not self.find:

            response = requests.get(
                f"http://{self.ip}:{self.port}/api/messages",
                headers={"Authorization": f"Bearer {token}"},
            )

            for message in response.json():
                body = message["body"]
                date = message["createdAt"]
                username = message["username"]
                id = message["id"]

                print(message)
                if username == self.__class__.__name__:
                    if datetime.fromisoformat(date) > datetime.fromisoformat(last['createdAt']):
                        last = message.copy()
                        print("coucou")

            print("fin")
            print(last)

            self.find = True
        print(last)
        self.num_commande += 1
        return last['body']





t = forum("192.168.56.1", 6000, "C2", "testtest")
t.execute("ls")
