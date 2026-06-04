import datetime
from pathlib import Path
import sys

import bcrypt
import pytest
import pymysql


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class InMemoryDatabase:
    def __init__(self):
        self.users = []
        self.shells = []
        self.shell_command_logs = []
        self.shell_machine_infos = []
        self.command_snippets = []
        self.notes = []
        self.credentials = []
        self.snippet_tags = []
        self.snippet_tag_links = set()
        self._ids = {
            "utilisateurs": 0,
            "shell": 0,
            "shell_command_log": 0,
            "shell_machine_info": 0,
            "command_snippet": 0,
            "note": 0,
            "credential": 0,
            "snippet_tag": 0,
        }
        self._clock = datetime.datetime(2026, 1, 1, 12, 0, 0)

    def connect(self):
        return FakeConnection(self)

    def next_id(self, table_name):
        self._ids[table_name] += 1
        return self._ids[table_name]

    def timestamp(self):
        self._clock += datetime.timedelta(seconds=1)
        return self._clock

    def seed_user(
        self,
        *,
        email,
        password="password123",
        username="user",
        nom="Nom",
        prenom="Prenom",
        is_admin=False,
        is_blocked=False,
        is_invited=False,
        expiration_date=None,
    ):
        user = {
            "id": self.next_id("utilisateurs"),
            "nom": nom,
            "prenom": prenom,
            "username": username,
            "email": email,
            "password": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()),
            "is_admin": is_admin,
            "is_blocked": is_blocked,
            "is_invited": is_invited,
            "expiration_date": expiration_date,
        }
        self.users.append(user)
        return user

    def seed_shell(self, *, user_id, nom="alpha", type_shell="shell"):
        shell = {
            "id": self.next_id("shell"),
            "id_proprietaire": user_id,
            "nom": nom,
            "type_shell": type_shell,
        }
        self.shells.append(shell)
        return shell

    def find_user_by_id(self, user_id):
        return next((user for user in self.users if user["id"] == user_id), None)

    def find_user_by_email(self, email):
        return next((user for user in self.users if user["email"] == email), None)


class FakeConnection:
    def __init__(self, db):
        self.db = db

    def cursor(self):
        return FakeCursor(self.db)

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        return None


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self._results = []
        self.lastrowid = None
        self.rowcount = 0

    def execute(self, sql, params=None):
        statement = " ".join(sql.lower().split())
        params = tuple(params or ())
        self._results = []
        self.lastrowid = None
        self.rowcount = 0

        if statement.startswith("insert into utilisateurs"):
            return self._insert_user(params)
        if "from utilisateurs" in statement and "where email" in statement:
            return self._select_user_by_email(params)
        if (
            "from utilisateurs" in statement
            and "where id = %s and is_invited = true" in statement
        ):
            return self._select_invited_user_by_id(params)
        if "from utilisateurs" in statement and "where is_invited = true" in statement:
            return self._select_invited_users()
        if "from utilisateurs" in statement and "where id = %s" in statement:
            return self._select_user_by_id(params)
        if statement.startswith("update utilisateurs set"):
            return self._update_user(params, statement)

        if statement.startswith("insert into command_snippet"):
            return self._insert_snippet(params)
        if "from command_snippet" in statement and "where id_proprietaire = %s" in statement:
            return self._select_snippets(params)
        if statement.startswith("insert into snippet_tag "):
            return self._upsert_snippet_tag(params)
        if statement.startswith("insert into snippet_tag_link"):
            return self._insert_snippet_tag_link(params)
        if "from snippet_tag_link" in statement and "inner join snippet_tag" in statement:
            return self._select_snippet_tags(params)
        if statement.startswith("delete from command_snippet"):
            return self._delete_owned_row(self.db.command_snippets, params)

        if statement.startswith("insert into note"):
            return self._insert_note(params)
        if "from note" in statement and "where id_proprietaire = %s" in statement:
            return self._select_notes(params)
        if statement.startswith("delete from note"):
            return self._delete_owned_row(self.db.notes, params)

        if statement.startswith("insert into credential"):
            return self._insert_credential(params)
        if "from credential" in statement and "where id_proprietaire = %s" in statement:
            return self._select_credentials(params)
        if statement.startswith("delete from credential"):
            return self._delete_owned_row(self.db.credentials, params)

        if statement.startswith("insert into shell "):
            return self._insert_shell(params)
        if "from shell s left join shell_machine_info smi" in statement:
            return self._select_machine_infos(params)
        if "from shell" in statement and "where id_proprietaire = %s and nom = %s" in statement:
            return self._select_shell_id_by_name(params)
        if "from shell" in statement and "where id = %s and id_proprietaire = %s" in statement:
            return self._select_shell_by_id_and_owner(params)
        if "from shell" in statement and "where id_proprietaire = %s" in statement:
            return self._select_shells(params)
        if statement.startswith("delete from shell"):
            return self._delete_shell(params)
        if statement.startswith("insert into shell_command_log"):
            return self._insert_shell_command_log(params)
        if statement.startswith("insert into shell_machine_info"):
            return self._upsert_shell_machine_info(params)

        raise AssertionError(f"Unhandled SQL in integration fake: {sql}")

    def fetchone(self):
        if not self._results:
            return None
        return dict(self._results[0])

    def fetchall(self):
        return [dict(row) for row in self._results]

    def _set_results(self, rows):
        self._results = [dict(row) for row in rows]
        self.rowcount = len(self._results)

    def _insert_user(self, params):
        prenom, nom, username, email, password, is_invited, expiration_date = params
        if self.db.find_user_by_email(email) is not None:
            raise pymysql.err.IntegrityError("duplicate email")

        self.lastrowid = self.db.next_id("utilisateurs")
        self.db.users.append(
            {
                "id": self.lastrowid,
                "nom": nom,
                "prenom": prenom,
                "username": username,
                "email": email,
                "password": password,
                "is_admin": False,
                "is_blocked": False,
                "is_invited": bool(is_invited),
                "expiration_date": expiration_date,
            }
        )
        self.rowcount = 1

    def _select_user_by_email(self, params):
        row = self.db.find_user_by_email(params[0])
        self._set_results([] if row is None else [row])

    def _select_user_by_id(self, params):
        row = self.db.find_user_by_id(params[0])
        self._set_results([] if row is None else [row])

    def _select_invited_user_by_id(self, params):
        row = self.db.find_user_by_id(params[0])
        if row is None or not row["is_invited"]:
            self._set_results([])
        else:
            self._set_results([row])

    def _select_invited_users(self):
        rows = [user for user in self.db.users if user["is_invited"]]
        rows.sort(key=lambda user: (user["expiration_date"] is None, user["expiration_date"], user["id"]))
        self._set_results(rows)

    def _update_user(self, params, statement):
        user_id = params[-1]
        row = self.db.find_user_by_id(user_id)
        if row is None:
            return

        value_index = 0
        if "is_blocked = %s" in statement:
            row["is_blocked"] = bool(params[value_index])
            value_index += 1
        if "expiration_date = %s" in statement:
            row["expiration_date"] = params[value_index]
        self.rowcount = 1

    def _insert_snippet(self, params):
        user_id, titre, commande, type_shell = params
        now = self.db.timestamp()
        self.lastrowid = self.db.next_id("command_snippet")
        self.db.command_snippets.append(
            {
                "id": self.lastrowid,
                "id_proprietaire": user_id,
                "titre": titre,
                "commande": commande,
                "type_shell": type_shell,
                "created_at": now,
                "updated_at": now,
            }
        )
        self.rowcount = 1

    def _select_snippets(self, params):
        user_id = params[0]
        rows = [
            {
                "id": row["id"],
                "titre": row["titre"],
                "contenu": row["commande"],
                "langage": row["type_shell"],
                "type_shell": row["type_shell"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in self.db.command_snippets
            if row["id_proprietaire"] == user_id
        ]
        rows.sort(key=lambda row: (row["created_at"], row["id"]), reverse=True)
        self._set_results(rows)

    def _upsert_snippet_tag(self, params):
        user_id, libelle = params
        existing = next(
            (
                tag
                for tag in self.db.snippet_tags
                if tag["id_proprietaire"] == user_id and tag["libelle"] == libelle
            ),
            None,
        )
        if existing:
            self.lastrowid = existing["id"]
            self.rowcount = 1
            return

        self.lastrowid = self.db.next_id("snippet_tag")
        self.db.snippet_tags.append(
            {"id": self.lastrowid, "id_proprietaire": user_id, "libelle": libelle}
        )
        self.rowcount = 1

    def _insert_snippet_tag_link(self, params):
        snippet_id, tag_id = params
        self.db.snippet_tag_links.add((snippet_id, tag_id))
        self.rowcount = 1

    def _select_snippet_tags(self, params):
        *snippet_ids, user_id = params
        rows = []
        for snippet_id, tag_id in self.db.snippet_tag_links:
            if snippet_id not in snippet_ids:
                continue
            tag = next((item for item in self.db.snippet_tags if item["id"] == tag_id), None)
            if tag and tag["id_proprietaire"] == user_id:
                rows.append({"snippet_id": snippet_id, "libelle": tag["libelle"]})
        rows.sort(key=lambda row: row["libelle"])
        self._set_results(rows)

    def _insert_note(self, params):
        user_id, titre, contenu = params
        now = self.db.timestamp()
        self.lastrowid = self.db.next_id("note")
        self.db.notes.append(
            {
                "id": self.lastrowid,
                "id_proprietaire": user_id,
                "titre": titre,
                "contenu": contenu,
                "created_at": now,
                "updated_at": now,
            }
        )
        self.rowcount = 1

    def _select_notes(self, params):
        user_id = params[0]
        rows = [
            {
                "id": row["id"],
                "titre": row["titre"],
                "contenu": row["contenu"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in self.db.notes
            if row["id_proprietaire"] == user_id
        ]
        rows.sort(key=lambda row: (row["created_at"], row["id"]), reverse=True)
        self._set_results(rows)

    def _insert_credential(self, params):
        user_id, nom, username, secret, is_encrypted = params
        now = self.db.timestamp()
        self.lastrowid = self.db.next_id("credential")
        self.db.credentials.append(
            {
                "id": self.lastrowid,
                "id_proprietaire": user_id,
                "nom": nom,
                "username": username,
                "secret": secret,
                "is_encrypted": is_encrypted,
                "created_at": now,
                "updated_at": now,
            }
        )
        self.rowcount = 1

    def _select_credentials(self, params):
        user_id = params[0]
        rows = [
            {
                "id": row["id"],
                "libelle": row["nom"],
                "nom": row["nom"],
                "identifiant": row["username"],
                "username": row["username"],
                "mot_de_passe": row["secret"],
                "secret": row["secret"],
                "is_encrypted": row["is_encrypted"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in self.db.credentials
            if row["id_proprietaire"] == user_id
        ]
        rows.sort(key=lambda row: (row["created_at"], row["id"]), reverse=True)
        self._set_results(rows)

    def _delete_owned_row(self, rows, params):
        item_id, user_id = params
        before = len(rows)
        rows[:] = [row for row in rows if not (row["id"] == item_id and row["id_proprietaire"] == user_id)]
        self.rowcount = before - len(rows)
        if rows is self.db.command_snippets:
            remaining_ids = {row["id"] for row in self.db.command_snippets}
            self.db.snippet_tag_links = {
                link for link in self.db.snippet_tag_links if link[0] in remaining_ids
            }

    def _insert_shell(self, params):
        user_id, nom, type_shell = params
        self.lastrowid = self.db.next_id("shell")
        self.db.shells.append(
            {
                "id": self.lastrowid,
                "id_proprietaire": user_id,
                "nom": nom,
                "type_shell": type_shell,
            }
        )
        self.rowcount = 1

    def _select_shell_id_by_name(self, params):
        user_id, nom = params
        rows = [
            shell
            for shell in self.db.shells
            if shell["id_proprietaire"] == user_id and shell["nom"] == nom
        ]
        rows.sort(key=lambda shell: shell["id"], reverse=True)
        self._set_results([] if not rows else [{"id": rows[0]["id"]}])

    def _select_shell_by_id_and_owner(self, params):
        shell_id, user_id = params
        row = next(
            (
                shell
                for shell in self.db.shells
                if shell["id"] == shell_id and shell["id_proprietaire"] == user_id
            ),
            None,
        )
        self._set_results([] if row is None else [row])

    def _select_shells(self, params):
        user_id = params[0]
        self._set_results([shell for shell in self.db.shells if shell["id_proprietaire"] == user_id])

    def _delete_shell(self, params):
        shell_id = params[0]
        before = len(self.db.shells)
        self.db.shells = [shell for shell in self.db.shells if shell["id"] != shell_id]
        self.rowcount = before - len(self.db.shells)

    def _insert_shell_command_log(self, params):
        shell_id, user_id, commande, sortie = params
        self.lastrowid = self.db.next_id("shell_command_log")
        self.db.shell_command_logs.append(
            {
                "id": self.lastrowid,
                "shell_id": shell_id,
                "id_proprietaire": user_id,
                "commande": commande,
                "sortie": sortie,
                "created_at": self.db.timestamp(),
            }
        )
        self.rowcount = 1

    def _upsert_shell_machine_info(self, params):
        shell_id, user_id, id_output, groups_output, users_output, uname_output, raw_payload = params
        row = next(
            (item for item in self.db.shell_machine_infos if item["shell_id"] == shell_id),
            None,
        )
        if row is None:
            now = self.db.timestamp()
            row = {
                "id": self.db.next_id("shell_machine_info"),
                "shell_id": shell_id,
                "id_proprietaire": user_id,
                "created_at": now,
            }
            self.db.shell_machine_infos.append(row)

        row.update(
            {
                "id_output": id_output,
                "groups_output": groups_output,
                "users_output": users_output,
                "uname_output": uname_output,
                "raw_payload": raw_payload,
                "updated_at": self.db.timestamp(),
            }
        )
        self.rowcount = 1

    def _select_machine_infos(self, params):
        user_id = params[0]
        rows = []
        for shell in self.db.shells:
            if shell["id_proprietaire"] != user_id:
                continue
            machine_info = next(
                (
                    item
                    for item in self.db.shell_machine_infos
                    if item["shell_id"] == shell["id"]
                ),
                {},
            )
            rows.append(
                {
                    "shell_id": shell["id"],
                    "shell_name": shell["nom"],
                    "type_shell": shell["type_shell"],
                    "id_output": machine_info.get("id_output"),
                    "groups_output": machine_info.get("groups_output"),
                    "users_output": machine_info.get("users_output"),
                    "uname_output": machine_info.get("uname_output"),
                    "created_at": machine_info.get("created_at"),
                    "updated_at": machine_info.get("updated_at"),
                }
            )
        rows.sort(key=lambda row: (row["shell_name"], row["shell_id"]))
        self._set_results(rows)


@pytest.fixture
def fake_db(monkeypatch):
    db = InMemoryDatabase()

    import DB
    import app.account_cleanup as account_cleanup
    import app.db_schema as db_schema
    import app.jwt_handler as jwt_handler

    monkeypatch.setattr(DB, "get_db_connection", db.connect)
    monkeypatch.setattr(jwt_handler, "get_db_connection", db.connect)
    monkeypatch.setattr(db_schema, "ensure_dashboard_tables", lambda: None)
    monkeypatch.setattr(account_cleanup, "delete_expired_accounts_if_due", lambda force=False: 0)
    return db


@pytest.fixture
def app(fake_db, monkeypatch):
    from app import create_app

    flask_app = create_app()
    flask_app.config.update(TESTING=True)

    import app.api.routes.signin as signin_route
    import app.api.routes.signup as signup_route
    import app.api.routes.dashboard.admin as admin_route
    import app.api.routes.dashboard.storage as storage_route
    import app.api.routes.dashboard.terminal as terminal_route

    for module in (signin_route, signup_route, admin_route, storage_route, terminal_route):
        monkeypatch.setattr(module, "get_db_connection", fake_db.connect)

    monkeypatch.setattr(storage_route, "ensure_dashboard_tables", lambda: None)
    monkeypatch.setattr(terminal_route, "ensure_dashboard_tables", lambda: None)
    terminal_route.instances.clear()

    yield flask_app

    terminal_route.instances.clear()


@pytest.fixture
def client(app):
    return app.test_client()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
