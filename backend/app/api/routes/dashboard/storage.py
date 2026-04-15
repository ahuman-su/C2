from flask import Blueprint, g, jsonify, request

from app.db_schema import ensure_dashboard_tables
from app.jwt_handler import token_required
from DB import get_db_connection


storage_bp = Blueprint("storage", __name__)


def _current_user_id():
    return g.user_data["user_id"]


def _clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _clean_port(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_bool(value):
    if isinstance(value, bool):
        return int(value)
    if value in (1, "1", "true", "True", "oui", "on"):
        return 1
    return 0


def _clean_tags(value):
    if value is None:
        return []

    if isinstance(value, str):
        raw_tags = value.split(",")
    elif isinstance(value, list):
        raw_tags = value
    else:
        raw_tags = []

    tags = []
    seen = set()
    for item in raw_tags:
        tag = _clean_text(item)
        if not tag:
            continue
        if len(tag) > 100:
            tag = tag[:100]
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        tags.append(tag)
    return tags


def _serialize_rows(rows):
    serialized = []
    for row in rows:
        item = dict(row)
        created_at = item.get("created_at")
        if created_at is not None:
            item["created_at"] = created_at.isoformat()
        serialized.append(item)
    return serialized


def _storage_payload(user_id):
    ensure_dashboard_tables()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                titre,
                commande AS contenu,
                description,
                type_shell AS langage,
                type_shell,
                created_at,
                updated_at
            FROM command_snippet
            WHERE id_proprietaire = %s
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,),
        )
        snippets = _serialize_rows(cursor.fetchall())

        snippet_ids = [snippet["id"] for snippet in snippets]
        snippet_tags = {}
        if snippet_ids:
            format_strings = ",".join(["%s"] * len(snippet_ids))
            cursor.execute(
                f"""
                SELECT
                    stl.snippet_id,
                    st.libelle
                FROM snippet_tag_link stl
                INNER JOIN snippet_tag st ON st.id = stl.tag_id
                WHERE stl.snippet_id IN ({format_strings}) AND st.id_proprietaire = %s
                ORDER BY st.libelle ASC
                """,
                (*snippet_ids, user_id),
            )
            for row in cursor.fetchall():
                snippet_tags.setdefault(row["snippet_id"], []).append(row["libelle"])

        for snippet in snippets:
            snippet["tags"] = snippet_tags.get(snippet["id"], [])

        cursor.execute(
            """
            SELECT
                id,
                titre,
                contenu,
                contexte,
                created_at,
                updated_at
            FROM note
            WHERE id_proprietaire = %s
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,),
        )
        notes = _serialize_rows(cursor.fetchall())

        cursor.execute(
            """
            SELECT
                id,
                nom AS libelle,
                nom,
                username AS identifiant,
                username,
                secret AS mot_de_passe,
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
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,),
        )
        passwords = _serialize_rows(cursor.fetchall())
    finally:
        conn.close()

    return {
        "snippets": snippets,
        "notes": notes,
        "passwords": passwords,
    }


@storage_bp.route("/storage", methods=["GET"])
@token_required
def get_storage():
    return jsonify(_storage_payload(_current_user_id()))


@storage_bp.route("/snippets", methods=["POST"])
@token_required
def create_snippet():
    ensure_dashboard_tables()

    data = request.get_json(silent=True) or {}
    titre = _clean_text(data.get("title"))
    commande = _clean_text(data.get("content") or data.get("commande"))
    description = _clean_text(data.get("description"))
    type_shell = _clean_text(data.get("type_shell") or data.get("language"))
    tags = _clean_tags(data.get("tags"))
    user_id = _current_user_id()

    if not titre or not commande:
        return jsonify({"message": "Le titre et le contenu du snippet sont requis."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO command_snippet (id_proprietaire, titre, commande, description, type_shell)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, titre, commande, description, type_shell),
        )
        snippet_id = cursor.lastrowid

        for tag in tags:
            cursor.execute(
                """
                INSERT INTO snippet_tag (id_proprietaire, libelle)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)
                """,
                (user_id, tag),
            )
            tag_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO snippet_tag_link (snippet_id, tag_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE snippet_id = snippet_id
                """,
                (snippet_id, tag_id),
            )

        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Snippet enregistre."}), 201


@storage_bp.route("/notes", methods=["POST"])
@token_required
def create_note():
    ensure_dashboard_tables()

    data = request.get_json(silent=True) or {}
    titre = _clean_text(data.get("title"))
    contenu = _clean_text(data.get("content"))
    contexte = _clean_text(data.get("context") or data.get("contexte"))

    if not titre or not contenu:
        return jsonify({"message": "Le titre et le contenu de la note sont requis."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO note (id_proprietaire, titre, contenu, contexte)
            VALUES (%s, %s, %s, %s)
            """,
            (_current_user_id(), titre, contenu, contexte),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Note enregistree."}), 201


@storage_bp.route("/passwords", methods=["POST"])
@token_required
def create_password():
    ensure_dashboard_tables()

    data = request.get_json(silent=True) or {}
    nom = _clean_text(data.get("label") or data.get("nom"))
    username = _clean_text(data.get("username"))
    secret = _clean_text(data.get("password") or data.get("secret"))
    type_credential = _clean_text(data.get("type_credential"))
    host = _clean_text(data.get("host"))
    port = _clean_port(data.get("port"))
    note_text = _clean_text(data.get("note"))
    is_encrypted = _clean_bool(data.get("is_encrypted"))

    if not nom or not secret:
        return jsonify({"message": "Le libelle et le mot de passe sont requis."}), 400

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
                _current_user_id(),
                nom,
                username,
                secret,
                type_credential,
                host,
                port,
                note_text,
                is_encrypted,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "Mot de passe enregistre."}), 201


def _delete_entry(table_name, item_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"DELETE FROM {table_name} WHERE id = %s AND id_proprietaire = %s",
            (item_id, user_id),
        )
        conn.commit()
        deleted = cursor.rowcount
    finally:
        conn.close()

    return deleted


@storage_bp.route("/snippets/<int:item_id>", methods=["DELETE"])
@token_required
def delete_snippet(item_id):
    ensure_dashboard_tables()
    deleted = _delete_entry("command_snippet", item_id, _current_user_id())
    if not deleted:
        return jsonify({"message": "Snippet introuvable."}), 404
    return jsonify({"message": "Snippet supprime."})


@storage_bp.route("/notes/<int:item_id>", methods=["DELETE"])
@token_required
def delete_note(item_id):
    ensure_dashboard_tables()
    deleted = _delete_entry("note", item_id, _current_user_id())
    if not deleted:
        return jsonify({"message": "Note introuvable."}), 404
    return jsonify({"message": "Note supprimee."})


@storage_bp.route("/passwords/<int:item_id>", methods=["DELETE"])
@token_required
def delete_password(item_id):
    ensure_dashboard_tables()
    deleted = _delete_entry("credential", item_id, _current_user_id())
    if not deleted:
        return jsonify({"message": "Mot de passe introuvable."}), 404
    return jsonify({"message": "Mot de passe supprime."})
