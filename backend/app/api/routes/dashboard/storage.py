import os

from cryptography.fernet import Fernet
from flask import Blueprint, g, jsonify, request

from app.jwt_handler import token_required
from DB import get_db_connection

storage = Blueprint("storage", __name__)


def _tags_from_payload(payload):
    tags = payload.get("tags", [])
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",")]
    cleaned = [tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()]

    unique = []
    seen = set()
    for tag in cleaned:
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(tag)
    return unique


def _format_datetime(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _snippet_payload_from_rows(rows):
    if not rows:
        return None

    first = rows[0]
    payload = {
        "id": first["id"],
        "id_proprietaire": first["id_proprietaire"],
        "titre": first["titre"],
        "commande": first["commande"],
        "description": first["description"],
        "type_shell": first["type_shell"],
        "created_at": _format_datetime(first.get("created_at")),
        "updated_at": _format_datetime(first.get("updated_at")),
        "tags": [],
    }

    for row in rows:
        label = row.get("tag_libelle")
        if label:
            payload["tags"].append(label)

    return payload


def _list_snippets_with_tags(cursor, user_id):
    cursor.execute(
        """
        SELECT
            s.id,
            s.id_proprietaire,
            s.titre,
            s.commande,
            s.description,
            s.type_shell,
            s.created_at,
            s.updated_at,
            t.libelle AS tag_libelle
        FROM command_snippet s
        LEFT JOIN snippet_tag_link l ON l.snippet_id = s.id
        LEFT JOIN snippet_tag t ON t.id = l.tag_id
        WHERE s.id_proprietaire = %s
        ORDER BY s.updated_at DESC, s.id DESC, t.libelle ASC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    if not rows:
        return []

    ordered = []
    grouped = {}
    for row in rows:
        snippet_id = row["id"]
        if snippet_id not in grouped:
            grouped[snippet_id] = {
                "id": row["id"],
                "id_proprietaire": row["id_proprietaire"],
                "titre": row["titre"],
                "commande": row["commande"],
                "description": row["description"],
                "type_shell": row["type_shell"],
                "created_at": _format_datetime(row.get("created_at")),
                "updated_at": _format_datetime(row.get("updated_at")),
                "tags": [],
            }
            ordered.append(snippet_id)

        label = row.get("tag_libelle")
        if label:
            grouped[snippet_id]["tags"].append(label)

    return [grouped[snippet_id] for snippet_id in ordered]


def _fetch_snippet_with_tags(cursor, user_id, snippet_id):
    cursor.execute(
        """
        SELECT
            s.id,
            s.id_proprietaire,
            s.titre,
            s.commande,
            s.description,
            s.type_shell,
            s.created_at,
            s.updated_at,
            t.libelle AS tag_libelle
        FROM command_snippet s
        LEFT JOIN snippet_tag_link l ON l.snippet_id = s.id
        LEFT JOIN snippet_tag t ON t.id = l.tag_id
        WHERE s.id = %s AND s.id_proprietaire = %s
        ORDER BY t.libelle ASC
        """,
        (snippet_id, user_id),
    )
    return _snippet_payload_from_rows(cursor.fetchall())


def _resolve_tags(cursor, user_id, tag_labels):
    tag_ids = []
    for label in tag_labels:
        cursor.execute(
            """
            SELECT id
            FROM snippet_tag
            WHERE id_proprietaire = %s AND libelle = %s
            """,
            (user_id, label),
        )
        existing = cursor.fetchone()
        if existing is None:
            cursor.execute(
                """
                INSERT INTO snippet_tag (id_proprietaire, libelle)
                VALUES (%s, %s)
                """,
                (user_id, label),
            )
            tag_ids.append(cursor.lastrowid)
        else:
            tag_ids.append(existing["id"])
    return tag_ids


def _replace_snippet_tags(cursor, snippet_id, tag_ids):
    cursor.execute("DELETE FROM snippet_tag_link WHERE snippet_id = %s", (snippet_id,))
    for tag_id in tag_ids:
        cursor.execute(
            """
            INSERT INTO snippet_tag_link (snippet_id, tag_id)
            VALUES (%s, %s)
            """,
            (snippet_id, tag_id),
        )


def _note_to_dict(row):
    return {
        "id": row["id"],
        "id_proprietaire": row["id_proprietaire"],
        "titre": row["titre"],
        "contenu": row["contenu"],
        "contexte": row["contexte"],
        "created_at": _format_datetime(row.get("created_at")),
        "updated_at": _format_datetime(row.get("updated_at")),
    }


def _get_fernet():
    key = os.getenv("CREDENTIALS_KEY")
    if not key:
        raise ValueError("CREDENTIALS_KEY manquant")
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)


def _encrypt_secret(secret):
    fernet = _get_fernet()
    return fernet.encrypt(secret.encode("utf-8")).decode("utf-8")


def _decrypt_secret(secret):
    fernet = _get_fernet()
    return fernet.decrypt(secret.encode("utf-8")).decode("utf-8")


def _credential_to_dict(row):
    secret_value = row["secret"]
    if row.get("is_encrypted"):
        try:
            secret_value = _decrypt_secret(row["secret"])
        except Exception as exc:
            print(f"Erreur decrypt secret: {exc}")
            secret_value = ""

    return {
        "id": row["id"],
        "id_proprietaire": row["id_proprietaire"],
        "nom": row["nom"],
        "username": row["username"],
        "secret": secret_value,
        "type_credential": row["type_credential"],
        "host": row["host"],
        "port": row["port"],
        "note": row["note"],
        "is_encrypted": bool(row.get("is_encrypted")),
        "created_at": _format_datetime(row.get("created_at")),
        "updated_at": _format_datetime(row.get("updated_at")),
    }


@storage.route("/snippets", methods=["GET"])
@token_required
def list_snippets():
    user_id = g.user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        payload = _list_snippets_with_tags(cursor, user_id)
    finally:
        conn.close()

    return jsonify(payload)


@storage.route("/snippets", methods=["POST"])
@token_required
def create_snippet():
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}
    titre = data.get("titre")
    commande = data.get("commande")

    if not titre or not commande:
        return jsonify({"error": "titre_et_commande_requis"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO command_snippet (id_proprietaire, titre, commande, description, type_shell)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                titre,
                commande,
                data.get("description"),
                data.get("type_shell"),
            ),
        )
        snippet_id = cursor.lastrowid

        tag_labels = _tags_from_payload(data)
        if tag_labels:
            tag_ids = _resolve_tags(cursor, user_id, tag_labels)
            _replace_snippet_tags(cursor, snippet_id, tag_ids)

        conn.commit()
        payload = _fetch_snippet_with_tags(cursor, user_id, snippet_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify(payload), 201


@storage.route("/snippets/<int:snippet_id>", methods=["PUT"])
@token_required
def update_snippet(snippet_id):
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, titre, commande
            FROM command_snippet
            WHERE id = %s AND id_proprietaire = %s
            """,
            (snippet_id, user_id),
        )
        snippet = cursor.fetchone()
        if snippet is None:
            return jsonify({"error": "snippet_introuvable"}), 404

        set_parts = []
        values = []

        if "titre" in data:
            set_parts.append("titre = %s")
            values.append(data.get("titre") or snippet["titre"])
        if "commande" in data:
            set_parts.append("commande = %s")
            values.append(data.get("commande") or snippet["commande"])
        if "description" in data:
            set_parts.append("description = %s")
            values.append(data.get("description"))
        if "type_shell" in data:
            set_parts.append("type_shell = %s")
            values.append(data.get("type_shell"))

        if set_parts:
            values.extend([snippet_id, user_id])
            cursor.execute(
                f"UPDATE command_snippet SET {', '.join(set_parts)} WHERE id = %s AND id_proprietaire = %s",
                tuple(values),
            )

        if "tags" in data:
            tag_labels = _tags_from_payload(data)
            tag_ids = _resolve_tags(cursor, user_id, tag_labels)
            _replace_snippet_tags(cursor, snippet_id, tag_ids)

        conn.commit()
        payload = _fetch_snippet_with_tags(cursor, user_id, snippet_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return jsonify(payload)


@storage.route("/snippets/<int:snippet_id>", methods=["DELETE"])
@token_required
def delete_snippet(snippet_id):
    user_id = g.user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id
            FROM command_snippet
            WHERE id = %s AND id_proprietaire = %s
            """,
            (snippet_id, user_id),
        )
        snippet = cursor.fetchone()
        if snippet is None:
            return jsonify({"error": "snippet_introuvable"}), 404

        cursor.execute(
            """
            DELETE FROM command_snippet
            WHERE id = %s AND id_proprietaire = %s
            """,
            (snippet_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True})


@storage.route("/notes", methods=["GET"])
@token_required
def list_notes():
    user_id = g.user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, id_proprietaire, titre, contenu, contexte, created_at, updated_at
            FROM note
            WHERE id_proprietaire = %s
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        )
        notes = cursor.fetchall()
    finally:
        conn.close()

    return jsonify([_note_to_dict(note) for note in notes])


@storage.route("/notes", methods=["POST"])
@token_required
def create_note():
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}
    titre = data.get("titre")
    contenu = data.get("contenu")
    if not titre or not contenu:
        return jsonify({"error": "titre_et_contenu_requis"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO note (id_proprietaire, titre, contenu, contexte)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, titre, contenu, data.get("contexte")),
        )
        note_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            """
            SELECT id, id_proprietaire, titre, contenu, contexte, created_at, updated_at
            FROM note
            WHERE id = %s AND id_proprietaire = %s
            """,
            (note_id, user_id),
        )
        note = cursor.fetchone()
    finally:
        conn.close()

    return jsonify(_note_to_dict(note)), 201


@storage.route("/notes/<int:note_id>", methods=["PUT"])
@token_required
def update_note(note_id):
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, titre, contenu
            FROM note
            WHERE id = %s AND id_proprietaire = %s
            """,
            (note_id, user_id),
        )
        note = cursor.fetchone()
        if note is None:
            return jsonify({"error": "note_introuvable"}), 404

        set_parts = []
        values = []

        if "titre" in data:
            set_parts.append("titre = %s")
            values.append(data.get("titre") or note["titre"])
        if "contenu" in data:
            set_parts.append("contenu = %s")
            values.append(data.get("contenu") or note["contenu"])
        if "contexte" in data:
            set_parts.append("contexte = %s")
            values.append(data.get("contexte"))

        if set_parts:
            values.extend([note_id, user_id])
            cursor.execute(
                f"UPDATE note SET {', '.join(set_parts)} WHERE id = %s AND id_proprietaire = %s",
                tuple(values),
            )

        conn.commit()
        cursor.execute(
            """
            SELECT id, id_proprietaire, titre, contenu, contexte, created_at, updated_at
            FROM note
            WHERE id = %s AND id_proprietaire = %s
            """,
            (note_id, user_id),
        )
        updated_note = cursor.fetchone()
    finally:
        conn.close()

    return jsonify(_note_to_dict(updated_note))


@storage.route("/notes/<int:note_id>", methods=["DELETE"])
@token_required
def delete_note(note_id):
    user_id = g.user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id
            FROM note
            WHERE id = %s AND id_proprietaire = %s
            """,
            (note_id, user_id),
        )
        note = cursor.fetchone()
        if note is None:
            return jsonify({"error": "note_introuvable"}), 404

        cursor.execute(
            """
            DELETE FROM note
            WHERE id = %s AND id_proprietaire = %s
            """,
            (note_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True})


@storage.route("/credentials", methods=["GET"])
@token_required
def list_credentials():
    user_id = g.user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                id,
                id_proprietaire,
                nom,
                username,
                secret,
                type_credential,
                host,
                port,
                note,
                is_encrypted,
                created_at,
                updated_at
            FROM credential
            WHERE id_proprietaire = %s
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        )
        creds = cursor.fetchall()
    finally:
        conn.close()

    return jsonify([_credential_to_dict(cred) for cred in creds])


@storage.route("/credentials", methods=["POST"])
@token_required
def create_credential():
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}
    nom = data.get("nom")
    secret = data.get("secret")
    if not nom or not secret:
        return jsonify({"error": "nom_et_secret_requis"}), 400
    try:
        encrypted_secret = _encrypt_secret(secret)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO credential (
                id_proprietaire,
                nom,
                username,
                secret,
                type_credential,
                host,
                port,
                note,
                is_encrypted
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                nom,
                data.get("username"),
                encrypted_secret,
                data.get("type_credential"),
                data.get("host"),
                data.get("port"),
                data.get("note"),
                1,
            ),
        )
        credential_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            """
            SELECT
                id,
                id_proprietaire,
                nom,
                username,
                secret,
                type_credential,
                host,
                port,
                note,
                is_encrypted,
                created_at,
                updated_at
            FROM credential
            WHERE id = %s AND id_proprietaire = %s
            """,
            (credential_id, user_id),
        )
        cred = cursor.fetchone()
    finally:
        conn.close()

    return jsonify(_credential_to_dict(cred)), 201


@storage.route("/credentials/<int:credential_id>", methods=["PUT"])
@token_required
def update_credential(credential_id):
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}

    encrypted_secret = None
    if data.get("secret"):
        try:
            encrypted_secret = _encrypt_secret(data.get("secret"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT
                id,
                nom,
                username,
                secret,
                type_credential,
                host,
                port,
                note,
                is_encrypted
            FROM credential
            WHERE id = %s AND id_proprietaire = %s
            """,
            (credential_id, user_id),
        )
        cred = cursor.fetchone()
        if cred is None:
            return jsonify({"error": "credential_introuvable"}), 404

        set_parts = []
        values = []

        if "nom" in data:
            set_parts.append("nom = %s")
            values.append(data.get("nom") or cred["nom"])
        if "username" in data:
            set_parts.append("username = %s")
            values.append(data.get("username"))
        if "secret" in data and encrypted_secret:
            set_parts.append("secret = %s")
            values.append(encrypted_secret)
            set_parts.append("is_encrypted = %s")
            values.append(1)
        if "type_credential" in data:
            set_parts.append("type_credential = %s")
            values.append(data.get("type_credential"))
        if "host" in data:
            set_parts.append("host = %s")
            values.append(data.get("host"))
        if "port" in data:
            set_parts.append("port = %s")
            values.append(data.get("port"))
        if "note" in data:
            set_parts.append("note = %s")
            values.append(data.get("note"))
        if "is_encrypted" in data:
            pass

        if set_parts:
            values.extend([credential_id, user_id])
            cursor.execute(
                f"UPDATE credential SET {', '.join(set_parts)} WHERE id = %s AND id_proprietaire = %s",
                tuple(values),
            )

        conn.commit()
        cursor.execute(
            """
            SELECT
                id,
                id_proprietaire,
                nom,
                username,
                secret,
                type_credential,
                host,
                port,
                note,
                is_encrypted,
                created_at,
                updated_at
            FROM credential
            WHERE id = %s AND id_proprietaire = %s
            """,
            (credential_id, user_id),
        )
        updated_cred = cursor.fetchone()
    finally:
        conn.close()

    return jsonify(_credential_to_dict(updated_cred))


@storage.route("/credentials/<int:credential_id>", methods=["DELETE"])
@token_required
def delete_credential(credential_id):
    user_id = g.user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id
            FROM credential
            WHERE id = %s AND id_proprietaire = %s
            """,
            (credential_id, user_id),
        )
        cred = cursor.fetchone()
        if cred is None:
            return jsonify({"error": "credential_introuvable"}), 404

        cursor.execute(
            """
            DELETE FROM credential
            WHERE id = %s AND id_proprietaire = %s
            """,
            (credential_id, user_id),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"success": True})
