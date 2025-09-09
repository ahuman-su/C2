# listener.py
import socket

HOST = '0.0.0.0'  # Écoute toutes les interfaces
PORT = 4444



class listener:
    def __init__(self,ip, port):
        self.ip = ip
        self.port = port

    def listen(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, PORT))
        self.server.listen(1)

        print(f"[+] En attente de connexion sur le port {PORT}...")
        self.client_socket, self.client_address = self.server.accept()
        print(f"[+] Connexion reçue de {self.client_address}")

    def execute(self, command):
        cmd = command
        self.client_socket.sendall(cmd.encode())
        result = self.client_socket.recv(4096).decode(errors='ignore')
        print(result)

    def break_connection(self):
        self.client_socket.close()
        self.server.close()

if __name__ == "__main__":
    lister1 = listener(HOST, PORT)
    lister1.listen()
    lister1.execute("exit")
    lister1.break_connection()