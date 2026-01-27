import os

from flask import Blueprint, jsonify, request, g
from sqlalchemy import select
from cryptography.fernet import Fernet

from app.jwt_handler import token_required
from DB import get_db_session
from DB.models import CommandSnippet, SnippetTag, Note, Credential

storage = Blueprint("storage", __name__)


def _tags_from_payload(payload):
    """Normalize tag payload to a unique list of strings (input: dict, output: list[str])."""
    tags = payload.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    cleaned = [t.strip() for t in tags if isinstance(t, str) and t.strip()]
    unique = []
    seen = set()
    for tag in cleaned:
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(tag)
    return unique


def _resolve_tags(session, user_id, tag_labels):
    """Ensure tags exist for user and return ORM objects (input: session, user_id, labels; output: list[SnippetTag])."""
    tags = []
    for label in tag_labels:
        existing = session.execute(
            select(SnippetTag).where(
                SnippetTag.id_proprietaire == user_id,
                SnippetTag.libelle == label,
            )
        ).scalar_one_or_none()
        if existing is None:
            existing = SnippetTag(id_proprietaire=user_id, libelle=label)
            session.add(existing)
            session.flush()
        tags.append(existing)
    return tags


def _snippet_to_dict(snippet):
    """Serialize CommandSnippet ORM to JSON-friendly dict (input: ORM; output: dict)."""
    return {
        "id": snippet.id,
        "id_proprietaire": snippet.id_proprietaire,
        "titre": snippet.titre,
        "commande": snippet.commande,
        "description": snippet.description,
        "type_shell": snippet.type_shell,
        "created_at": snippet.created_at.isoformat() if snippet.created_at else None,
        "updated_at": snippet.updated_at.isoformat() if snippet.updated_at else None,
        "tags": [tag.libelle for tag in snippet.tags],
    }


def _note_to_dict(note):
    """Serialize Note ORM to JSON-friendly dict (input: ORM; output: dict)."""
    return {
        "id": note.id,
        "id_proprietaire": note.id_proprietaire,
        "titre": note.titre,
        "contenu": note.contenu,
        "contexte": note.contexte,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
    }


def _credential_to_dict(credential):
    """Serialize Credential ORM to dict with decrypted secret if possible (input: ORM; output: dict)."""
    secret_value = credential.secret
    if credential.is_encrypted:
        try:
            secret_value = _decrypt_secret(credential.secret)
        except Exception as exc:
            print(f"Erreur decrypt secret: {exc}")
            secret_value = ""
    return {
        "id": credential.id,
        "id_proprietaire": credential.id_proprietaire,
        "nom": credential.nom,
        "username": credential.username,
        "secret": secret_value,
        "type_credential": credential.type_credential,
        "host": credential.host,
        "port": credential.port,
        "note": credential.note,
        "is_encrypted": bool(credential.is_encrypted),
        "created_at": credential.created_at.isoformat() if credential.created_at else None,
        "updated_at": credential.updated_at.isoformat() if credential.updated_at else None,
    }


def _get_fernet():
    """Build Fernet from env key CREDENTIALS_KEY (input: env; output: Fernet)."""
    key = os.getenv("CREDENTIALS_KEY")
    if not key:
        raise ValueError("CREDENTIALS_KEY manquant")
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)


def _encrypt_secret(secret):
    """Encrypt secret using Fernet (input: str; output: str token)."""
    fernet = _get_fernet()
    return fernet.encrypt(secret.encode("utf-8")).decode("utf-8")


def _decrypt_secret(secret):
    """Decrypt secret using Fernet (input: str token; output: str)."""
    fernet = _get_fernet()
    return fernet.decrypt(secret.encode("utf-8")).decode("utf-8")


@storage.route("/snippets", methods=["GET"])
@token_required
def list_snippets():
    """GET /snippets -> list current user's snippets (output: list[dict])."""
    user_id = g.user_data["user_id"]
    with get_db_session() as session:
        snippets = session.execute(
            select(CommandSnippet)
            .where(CommandSnippet.id_proprietaire == user_id)
            .order_by(CommandSnippet.updated_at.desc())
        ).scalars().all()
        payload = [_snippet_to_dict(snippet) for snippet in snippets]
    return jsonify(payload)


@storage.route("/snippets", methods=["POST"])
@token_required
def create_snippet():
    """POST /snippets with JSON fields -> create snippet (output: snippet dict)."""
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}
    titre = data.get("titre")
    commande = data.get("commande")

    if not titre or not commande:
        return jsonify({"error": "titre_et_commande_requis"}), 400

    with get_db_session() as session:
        snippet = CommandSnippet(
            id_proprietaire=user_id,
            titre=titre,
            commande=commande,
            description=data.get("description"),
            type_shell=data.get("type_shell"),
        )
        tag_labels = _tags_from_payload(data)
        if tag_labels:
            snippet.tags = _resolve_tags(session, user_id, tag_labels)

        session.add(snippet)
        session.flush()
        payload = _snippet_to_dict(snippet)

    return jsonify(payload), 201


@storage.route("/snippets/<int:snippet_id>", methods=["PUT"])
@token_required
def update_snippet(snippet_id):
    """PUT /snippets/<id> with JSON fields -> update snippet (output: snippet dict)."""
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}

    with get_db_session() as session:
        snippet = session.execute(
            select(CommandSnippet).where(
                CommandSnippet.id == snippet_id,
                CommandSnippet.id_proprietaire == user_id,
            )
        ).scalar_one_or_none()
        if snippet is None:
            return jsonify({"error": "snippet_introuvable"}), 404

        if "titre" in data:
            snippet.titre = data.get("titre") or snippet.titre
        if "commande" in data:
            snippet.commande = data.get("commande") or snippet.commande
        if "description" in data:
            snippet.description = data.get("description")
        if "type_shell" in data:
            snippet.type_shell = data.get("type_shell")


        if "tags" in data:
            tag_labels = _tags_from_payload(data)
            snippet.tags = _resolve_tags(session, user_id, tag_labels)

        session.flush()
        payload = _snippet_to_dict(snippet)

    return jsonify(payload)


@storage.route("/snippets/<int:snippet_id>", methods=["DELETE"])
@token_required
def delete_snippet(snippet_id):
    """DELETE /snippets/<id> -> delete snippet (output: success bool)."""
    user_id = g.user_data["user_id"]
    with get_db_session() as session:
        snippet = session.execute(
            select(CommandSnippet).where(
                CommandSnippet.id == snippet_id,
                CommandSnippet.id_proprietaire == user_id,
            )
        ).scalar_one_or_none()
        if snippet is None:
            return jsonify({"error": "snippet_introuvable"}), 404
        session.delete(snippet)
    return jsonify({"success": True})


@storage.route("/notes", methods=["GET"])
@token_required
def list_notes():
    """GET /notes -> list current user's notes (output: list[dict])."""
    user_id = g.user_data["user_id"]
    with get_db_session() as session:
        notes = session.execute(
            select(Note)
            .where(Note.id_proprietaire == user_id)
            .order_by(Note.updated_at.desc())
        ).scalars().all()
        payload = [_note_to_dict(note) for note in notes]
    return jsonify(payload)


@storage.route("/notes", methods=["POST"])
@token_required
def create_note():
    """POST /notes with JSON fields -> create note (output: note dict)."""
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}
    titre = data.get("titre")
    contenu = data.get("contenu")
    if not titre or not contenu:
        return jsonify({"error": "titre_et_contenu_requis"}), 400

    with get_db_session() as session:
        note = Note(
            id_proprietaire=user_id,
            titre=titre,
            contenu=contenu,
            contexte=data.get("contexte"),
        )
        session.add(note)
        session.flush()
        payload = _note_to_dict(note)

    return jsonify(payload), 201


@storage.route("/notes/<int:note_id>", methods=["PUT"])
@token_required
def update_note(note_id):
    """PUT /notes/<id> with JSON fields -> update note (output: note dict)."""
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}

    with get_db_session() as session:
        note = session.execute(
            select(Note).where(
                Note.id == note_id,
                Note.id_proprietaire == user_id,
            )
        ).scalar_one_or_none()
        if note is None:
            return jsonify({"error": "note_introuvable"}), 404

        if "titre" in data:
            note.titre = data.get("titre") or note.titre
        if "contenu" in data:
            note.contenu = data.get("contenu") or note.contenu
        if "contexte" in data:
            note.contexte = data.get("contexte")

        session.flush()
        payload = _note_to_dict(note)

    return jsonify(payload)


@storage.route("/notes/<int:note_id>", methods=["DELETE"])
@token_required
def delete_note(note_id):
    """DELETE /notes/<id> -> delete note (output: success bool)."""
    user_id = g.user_data["user_id"]
    with get_db_session() as session:
        note = session.execute(
            select(Note).where(
                Note.id == note_id,
                Note.id_proprietaire == user_id,
            )
        ).scalar_one_or_none()
        if note is None:
            return jsonify({"error": "note_introuvable"}), 404
        session.delete(note)
    return jsonify({"success": True})


@storage.route("/credentials", methods=["GET"])
@token_required
def list_credentials():
    """GET /credentials -> list current user's credentials (output: list[dict])."""
    user_id = g.user_data["user_id"]
    with get_db_session() as session:
        creds = session.execute(
            select(Credential)
            .where(Credential.id_proprietaire == user_id)
            .order_by(Credential.updated_at.desc())
        ).scalars().all()
        payload = [_credential_to_dict(cred) for cred in creds]
    return jsonify(payload)


@storage.route("/credentials", methods=["POST"])
@token_required
def create_credential():
    """POST /credentials with JSON fields -> create credential (output: credential dict)."""
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

    with get_db_session() as session:
        cred = Credential(
            id_proprietaire=user_id,
            nom=nom,
            username=data.get("username"),
            secret=encrypted_secret,
            type_credential=data.get("type_credential"),
            host=data.get("host"),
            port=data.get("port"),
            note=data.get("note"),
            is_encrypted=True,
        )
        session.add(cred)
        session.flush()
        payload = _credential_to_dict(cred)

    return jsonify(payload), 201


@storage.route("/credentials/<int:credential_id>", methods=["PUT"])
@token_required
def update_credential(credential_id):
    """PUT /credentials/<id> with JSON fields -> update credential (output: credential dict)."""
    user_id = g.user_data["user_id"]
    data = request.get_json() or {}
    encrypted_secret = None
    if data.get("secret"):
        try:
            encrypted_secret = _encrypt_secret(data.get("secret"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    with get_db_session() as session:
        cred = session.execute(
            select(Credential).where(
                Credential.id == credential_id,
                Credential.id_proprietaire == user_id,
            )
        ).scalar_one_or_none()
        if cred is None:
            return jsonify({"error": "credential_introuvable"}), 404

        if "nom" in data:
            cred.nom = data.get("nom") or cred.nom
        if "username" in data:
            cred.username = data.get("username")
        if "secret" in data:
            if encrypted_secret:
                cred.secret = encrypted_secret
        if "type_credential" in data:
            cred.type_credential = data.get("type_credential")
        if "host" in data:
            cred.host = data.get("host")
        if "port" in data:
            cred.port = data.get("port")
        if "note" in data:
            cred.note = data.get("note")
        if "is_encrypted" in data:
            pass

        session.flush()
        payload = _credential_to_dict(cred)

    return jsonify(payload)


@storage.route("/credentials/<int:credential_id>", methods=["DELETE"])
@token_required
def delete_credential(credential_id):
    """DELETE /credentials/<id> -> delete credential (output: success bool)."""
    user_id = g.user_data["user_id"]
    with get_db_session() as session:
        cred = session.execute(
            select(Credential).where(
                Credential.id == credential_id,
                Credential.id_proprietaire == user_id,
            )
        ).scalar_one_or_none()
        if cred is None:
            return jsonify({"error": "credential_introuvable"}), 404
        session.delete(cred)
    return jsonify({"success": True})
