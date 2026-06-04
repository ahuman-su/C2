import datetime
import json

import pytest
import requests

from app.jwt_handler import generate_token


class FakeShell:
    def __init__(self, outputs):
        self.outputs = outputs
        self.commands = []

    def execute(self, command, timeout_seconds=None):
        self.commands.append((command, timeout_seconds))
        return self.outputs[command]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def signup_payload(email="alice@example.test", password="secret123"):
    return {
        "prenom": "Alice",
        "nom": "Admin",
        "username": "alice",
        "email": email,
        "password": password,
    }


def create_signed_in_user(client, payload=None):
    payload = payload or signup_payload()
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    return payload, body["token"]


def test_auth_signup_signin_and_check_token_flow(client, fake_db):
    payload, signup_token = create_signed_in_user(client)

    assert len(fake_db.users) == 1
    assert fake_db.users[0]["email"] == payload["email"]
    assert fake_db.users[0]["is_invited"] is False

    check_response = client.get("/api/check-token", headers=auth_headers(signup_token))

    assert check_response.status_code == 200
    assert check_response.get_json() == {"valid": True}

    signin_response = client.post(
        "/auth/signin",
        json={"email": payload["email"], "password": payload["password"]},
    )

    assert signin_response.status_code == 200
    assert signin_response.get_json()["success"] is True
    assert signin_response.get_json()["token"]

    invalid_response = client.get("/api/check-token", headers=auth_headers("invalid-token"))

    assert invalid_response.status_code == 401
    assert invalid_response.get_json()["valid"] is False


def test_storage_crud_flow_is_scoped_to_authenticated_user(client, fake_db):
    _, token = create_signed_in_user(client)

    unauthorized_response = client.get("/dashboard/storage")
    assert unauthorized_response.status_code == 401

    snippet_response = client.post(
        "/dashboard/snippets",
        headers=auth_headers(token),
        json={
            "title": "Recon",
            "content": "whoami",
            "language": "linux",
            "tags": ["enum", "linux", "enum", ""],
        },
    )
    note_response = client.post(
        "/dashboard/notes",
        headers=auth_headers(token),
        json={"title": "Compte rendu", "content": "Privilege escalation possible"},
    )
    password_response = client.post(
        "/dashboard/passwords",
        headers=auth_headers(token),
        json={"label": "forum", "username": "operator", "password": "s3cret"},
    )

    assert snippet_response.status_code == 201
    assert note_response.status_code == 201
    assert password_response.status_code == 201

    storage_response = client.get("/dashboard/storage", headers=auth_headers(token))

    assert storage_response.status_code == 200
    storage = storage_response.get_json()
    assert storage["snippets"][0]["titre"] == "Recon"
    assert storage["snippets"][0]["contenu"] == "whoami"
    assert storage["snippets"][0]["tags"] == ["enum", "linux"]
    assert storage["notes"][0]["titre"] == "Compte rendu"
    assert storage["passwords"][0]["libelle"] == "forum"

    snippet_id = storage["snippets"][0]["id"]
    delete_response = client.delete(f"/dashboard/snippets/{snippet_id}", headers=auth_headers(token))
    missing_response = client.delete(f"/dashboard/snippets/{snippet_id}", headers=auth_headers(token))

    assert delete_response.status_code == 200
    assert missing_response.status_code == 404
    assert client.get("/dashboard/storage", headers=auth_headers(token)).get_json()["snippets"] == []


def test_admin_invited_user_lifecycle_requires_admin_token(client, fake_db):
    admin = fake_db.seed_user(
        email="admin@example.test",
        password="admin-pass",
        username="admin",
        is_admin=True,
    )
    invited = fake_db.seed_user(
        email="invite@example.test",
        password="guest-pass",
        username="guest",
        is_invited=True,
        expiration_date=datetime.datetime.now() + datetime.timedelta(hours=2),
    )
    admin_token = generate_token(admin["id"])
    invited_token = generate_token(invited["id"])

    forbidden_response = client.get(
        "/dashboard/admin/invited-users",
        headers=auth_headers(invited_token),
    )
    list_response = client.get(
        "/dashboard/admin/invited-users",
        headers=auth_headers(admin_token),
    )
    update_response = client.patch(
        f"/dashboard/admin/invited-users/{invited['id']}",
        headers=auth_headers(admin_token),
        json={"is_blocked": True, "add_hours": 1},
    )
    signin_response = client.post(
        "/auth/signin",
        json={"email": "invite@example.test", "password": "guest-pass"},
    )

    assert forbidden_response.status_code == 403
    assert list_response.status_code == 200
    assert list_response.get_json()["users"][0]["email"] == "invite@example.test"
    assert update_response.status_code == 200
    assert update_response.get_json()["user"]["status"] == "blocked"
    assert signin_response.status_code == 403
    assert signin_response.get_json()["message"] == "Compte bloque"


def test_terminal_command_and_system_probe_store_outputs(client, fake_db):
    user = fake_db.seed_user(email="operator@example.test", password="operator-pass")
    fake_db.seed_shell(user_id=user["id"], nom="alpha")
    token = generate_token(user["id"])

    import app.api.routes.dashboard.terminal as terminal_route

    terminal_route.instances["alpha"] = FakeShell(
        {
            "whoami": "root\n",
            "system_probe": (
                terminal_route.SYSTEM_PROBE_PREFIX
                + json.dumps(
                    {
                        "id": "uid=0(root)",
                        "groups": "root sudo",
                        "users": "root alice",
                        "uname": "Linux target 6.1",
                    }
                )
            ),
        }
    )

    command_response = client.post(
        "/dashboard/terminal",
        headers=auth_headers(token),
        json={"commande": "whoami", "shell": ["alpha"]},
    )
    probe_response = client.post(
        "/dashboard/terminal",
        headers=auth_headers(token),
        json={"commande": "system_probe", "shell": ["alpha"]},
    )
    machine_info_response = client.get("/dashboard/machine_info", headers=auth_headers(token))

    assert command_response.status_code == 200
    assert command_response.get_json()["resulat"] == {"alpha": "root<br>"}
    assert fake_db.shell_command_logs[0]["commande"] == "whoami"
    assert fake_db.shell_command_logs[0]["sortie"] == "root\n"

    assert probe_response.status_code == 200
    assert "uid=0(root)" in probe_response.get_json()["resulat"]["alpha"]
    assert fake_db.shell_machine_infos[0]["uname_output"] == "Linux target 6.1"

    assert machine_info_response.status_code == 200
    machine_info = machine_info_response.get_json()[0]
    assert machine_info["shell_name"] == "alpha"
    assert machine_info["users_output"] == "root alice"


def test_pwned_password_endpoint_maps_service_results(client, fake_db, monkeypatch):
    user = fake_db.seed_user(email="security@example.test", password="security-pass")
    token = generate_token(user["id"])

    import app.api.routes.dashboard.hibp as hibp_route

    monkeypatch.setattr(hibp_route, "lookup_password_exposure", lambda password: 42)
    exposed_response = client.post(
        "/dashboard/pwned-password",
        headers=auth_headers(token),
        json={"password": "password"},
    )

    def unavailable(_password):
        raise requests.RequestException("offline")

    monkeypatch.setattr(hibp_route, "lookup_password_exposure", unavailable)
    unavailable_response = client.post(
        "/dashboard/pwned-password",
        headers=auth_headers(token),
        json={"password": "password"},
    )

    assert exposed_response.status_code == 200
    assert exposed_response.get_json()["exposed"] is True
    assert exposed_response.get_json()["severity"] == "danger"
    assert unavailable_response.status_code == 503


@pytest.mark.parametrize(
    "payload, expected_message",
    [
        ({}, "Champs requis manquants"),
        ({**signup_payload(), "expiration_hours": "zero"}, "Duree invalide"),
        ({**signup_payload(), "expiration_hours": 0}, "La duree doit etre superieure"),
    ],
)
def test_signup_rejects_invalid_payloads(client, payload, expected_message):
    response = client.post("/auth/signup", json=payload)

    assert response.status_code == 400
    assert expected_message in response.get_json()["message"]
