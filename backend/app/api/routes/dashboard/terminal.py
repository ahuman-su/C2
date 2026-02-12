from flask import Blueprint, g, jsonify, request

from app.jwt_handler import token_required
from DB import get_db_connection
from .shell import Forum, Pastbin, Shell

terminal = Blueprint("dashboard", __name__)
listener = Blueprint("listener", __name__)
shells_list_bp = Blueprint("shells_list", __name__)
supprimer_shell_bp = Blueprint("supprimer_shell", __name__)

instances = {}
shell_temp = {}


@terminal.route("/terminal", methods=["GET", "POST"])
@token_required
def terminal_command():
    data = request.get_json()

    command = data["commande"]
    shell_user = data["shell"]
    results = {}
    log_entries = []
    user_data = g.user_data
    user_id = user_data["user_id"]

    # on boucle sur l'ensemble des shell ou l'on veux executer la commade
    for shell_name in shell_user:
        shell_instance = instances[shell_name]
        try:
            output = shell_instance.execute(command)
        except Exception as exc:
            output = f"Erreur: {str(exc)}"

        # Transforme les sauts de ligne en <br> pour un affichage HTML correct
        raw_output = output
        output = raw_output.replace("\n", "<br>")

        results[shell_name] = output
        log_entries.append((shell_name, raw_output))

    if log_entries:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            for shell_name, raw_output in log_entries:
                cursor.execute(
                    """
                    SELECT id
                    FROM shell
                    WHERE id_proprietaire = %s AND nom = %s
                    """,
                    (user_id, shell_name),
                )
                shell_row = cursor.fetchone()
                shell_id = shell_row["id"] if shell_row else None

                cursor.execute(
                    """
                    INSERT INTO shell_command_log (shell_id, id_proprietaire, commande, sortie)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (shell_id, user_id, command, raw_output),
                )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            print(f"Erreur log commandes: {exc}")
        finally:
            conn.close()

    return jsonify({"resulat": results})


@listener.route("/listener", methods=["POST"])
@token_required
def listener_command():
    data = request.get_json()
    print(data)
    nom = data["nom"]
    ip = data["host"]
    port = data["port"]
    types = data["type"]
    user = data["user"]
    password = data["password"]
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

        else:
            print("erreur de connexion")

        return jsonify({"resulat": "sa fcontion"})

    if types == "Pastbin":
        instances[nom] = Pastbin(nom)
        save_shell_to_db(user_id, nom, "Pastbin")
        print("nom :", nom)

        return jsonify({"resulat": "sa fcontion"})

    if types == "forume":
        instances[nom] = Forum(ip, port, user, password, nom)
        save_shell_to_db(user_id, nom, "Forum")
        print("nom :", nom)

        return jsonify({"resulat": "sa fcontion"})

    print("erreur")
    return jsonify({"resulat": "erreur"})


@shells_list_bp.route("/shells_list", methods=["GET", "POST"])
@token_required
def shells_list():
    user_data = g.user_data
    user_id = user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT *
            FROM shell
            WHERE id_proprietaire = %s
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(rows)


@supprimer_shell_bp.route("/supprimer_shell", methods=["POST"])
@token_required
def supprimer_shell():
    data = request.get_json()
    shell_id = data["id"]

    user_data = g.user_data
    user_id = user_data["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT *
            FROM shell
            WHERE id = %s AND id_proprietaire = %s
            """,
            (shell_id, user_id),
        )

        row = cursor.fetchone()
        if row is not None:
            cursor.execute("DELETE FROM shell WHERE id = %s", (row["id"],))
            conn.commit()
            print("supprimer ", row["nom"], " de la DB")
    finally:
        conn.close()

    return jsonify({"resulat": "supprimer"})



def save_shell_to_db(user_id, nom, type_shell):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO shell (id_proprietaire, nom, type_shell)
            VALUES (%s, %s, %s)
            """,
            (user_id, nom, type_shell),
        )
        conn.commit()
    finally:
        conn.close()
