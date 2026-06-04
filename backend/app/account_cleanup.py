import os
import threading
import time

from DB import get_db_connection
from app.jwt_handler import local_now


_cleanup_lock = threading.Lock()
_last_cleanup_run = 0.0


def _cleanup_interval_seconds():
    try:
        return max(
            0,
            int(os.getenv("EXPIRED_ACCOUNT_CLEANUP_INTERVAL_SECONDS", "60")),
        )
    except ValueError:
        return 60


def _placeholders(values):
    return ", ".join(["%s"] * len(values))


def _delete_owned_rows(cursor, table_name, user_ids):
    placeholders = _placeholders(user_ids)
    cursor.execute(
        f"DELETE FROM {table_name} WHERE id_proprietaire IN ({placeholders})",
        user_ids,
    )


def delete_expired_accounts(now=None):
    now = now or local_now()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM utilisateurs
            WHERE expiration_date IS NOT NULL
              AND expiration_date <= %s
            FOR UPDATE
            """,
            (now,),
        )
        user_ids = tuple(row["id"] for row in cursor.fetchall())

        if not user_ids:
            conn.commit()
            return 0

        placeholders = _placeholders(user_ids)

        cursor.execute(
            f"""
            DELETE stl
            FROM snippet_tag_link AS stl
            LEFT JOIN command_snippet AS cs ON cs.id = stl.snippet_id
            LEFT JOIN snippet_tag AS st ON st.id = stl.tag_id
            WHERE cs.id_proprietaire IN ({placeholders})
               OR st.id_proprietaire IN ({placeholders})
            """,
            (*user_ids, *user_ids),
        )

        cursor.execute(
            f"""
            DELETE scl
            FROM shell_command_log AS scl
            LEFT JOIN shell AS s ON s.id = scl.shell_id
            WHERE scl.id_proprietaire IN ({placeholders})
               OR s.id_proprietaire IN ({placeholders})
            """,
            (*user_ids, *user_ids),
        )

        cursor.execute(
            f"""
            DELETE smi
            FROM shell_machine_info AS smi
            LEFT JOIN shell AS s ON s.id = smi.shell_id
            WHERE smi.id_proprietaire IN ({placeholders})
               OR s.id_proprietaire IN ({placeholders})
            """,
            (*user_ids, *user_ids),
        )

        for table_name in (
            "command_snippet",
            "note",
            "credential",
            "snippet_tag",
            "shell",
        ):
            _delete_owned_rows(cursor, table_name, user_ids)

        cursor.execute(
            f"DELETE FROM utilisateurs WHERE id IN ({placeholders})",
            user_ids,
        )
        deleted_accounts = cursor.rowcount
        conn.commit()
        return deleted_accounts
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_expired_accounts_if_due(force=False):
    global _last_cleanup_run

    interval_seconds = _cleanup_interval_seconds()
    current_time = time.monotonic()
    if (
        not force and interval_seconds > 0
        and current_time - _last_cleanup_run < interval_seconds
    ):
        return 0

    if not _cleanup_lock.acquire(blocking=False):
        return 0

    try:
        current_time = time.monotonic()
        if (
            not force and interval_seconds > 0
            and current_time - _last_cleanup_run < interval_seconds
        ):
            return 0
        return delete_expired_accounts()
    finally:
        _last_cleanup_run = time.monotonic()
        _cleanup_lock.release()
