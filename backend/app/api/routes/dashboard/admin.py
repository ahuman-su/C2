import datetime
from flask import Blueprint, jsonify, request, g
from DB import get_db_connection
from app.jwt_handler import admin_required
from app.jwt_handler import normalize_datetime
from app.jwt_handler import serialize_datetime
from app.jwt_handler import local_now

admin_bp = Blueprint('dashboard-admin', __name__)


def _parse_boolean(value):
    if isinstance(value, bool): #isintance c'est le type de variable
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "1", "yes", "on"):
            return True
        if normalized in ("false", "0", "no", "off"):
            return False
    raise ValueError("is_blocked doit etre un booleen.")


def _parse_hours(value):
    try:
        hours = int(value)
    except (TypeError, ValueError):
        raise ValueError("add_hours doit etre un nombre d'heures.")

    if hours <= 0:
        raise ValueError("add_hours doit etre superieur a zero.")
    return hours


def _extend_expiration_date(expiration_date, hours):
    now = local_now()
    expiration_date = normalize_datetime(expiration_date)
    start_date = expiration_date if expiration_date and expiration_date > now else now
    return start_date + datetime.timedelta(hours=hours)


def _serialize_invited_user(row, now=None):
    now = now or local_now()
    expiration_date = normalize_datetime(row["expiration_date"])
    is_blocked = bool(row["is_blocked"])
    is_expired = expiration_date is not None and expiration_date <= now

    if is_blocked:
        status = "blocked"
    elif is_expired:
        status = "expired"
    else:
        status = "active"

    remaining_seconds = None
    if expiration_date is not None:
        remaining_seconds = max(0, int((expiration_date - now).total_seconds()))

    return {
        "id": row["id"],
        "nom": row["nom"],
        "prenom": row["prenom"],
        "username": row["username"],
        "email": row["email"],
        "is_blocked": is_blocked,
        "is_invited": bool(row["is_invited"]),
        "is_expired": is_expired,
        "status": status,
        "expiration_date": serialize_datetime(expiration_date),
        "remaining_seconds": remaining_seconds,
    }


@admin_bp.route('/admin/invited-users', methods=['GET'])
@admin_required
def list_invited_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                username,
                email,
                is_blocked,
                is_invited,
                expiration_date
            FROM utilisateurs
            WHERE is_invited = TRUE
            ORDER BY expiration_date ASC, id ASC
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    now = local_now()
    return jsonify({
        "success": True,
        "users": [_serialize_invited_user(row, now) for row in rows],
    })


@admin_bp.route('/admin/invited-users/<int:user_id>', methods=['PATCH'])
@admin_required
def update_invited_user(user_id):
    data = request.get_json() or {}
    if "is_blocked" not in data and "add_hours" not in data:
        return jsonify({
            "success": False,
            "message": "is_blocked ou add_hours est requis.",
        }), 400

    is_blocked = None
    add_hours = None

    if "is_blocked" in data:
        try:
            is_blocked = _parse_boolean(data["is_blocked"])
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400

    if "add_hours" in data:
        try:
            add_hours = _parse_hours(data["add_hours"])
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400

    if user_id == g.user_data["user_id"] and is_blocked:
        return jsonify({
            "success": False,
            "message": "Impossible de bloquer le compte administrateur courant.",
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                username,
                email,
                is_blocked,
                is_invited,
                expiration_date
            FROM utilisateurs
            WHERE id = %s AND is_invited = TRUE
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return jsonify({"success": False, "message": "Utilisateur invite introuvable."}), 404

        updates = []
        params = []
        if is_blocked is not None:
            updates.append("is_blocked = %s")
            params.append(is_blocked)
        if add_hours is not None:
            updates.append("expiration_date = %s")
            params.append(_extend_expiration_date(row["expiration_date"], add_hours))

        cursor.execute(
            f"UPDATE utilisateurs SET {', '.join(updates)} WHERE id = %s",
            (*params, user_id),
        )
        conn.commit()

        cursor.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                username,
                email,
                is_blocked,
                is_invited,
                expiration_date
            FROM utilisateurs
            WHERE id = %s
            """,
            (user_id,),
        )
        updated_row = cursor.fetchone()
    finally:
        conn.close()

    return jsonify({
        "success": True,
        "user": _serialize_invited_user(updated_row),
    })
