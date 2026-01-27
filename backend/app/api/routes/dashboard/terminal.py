from flask import request, jsonify, Blueprint, g
import jwt
from sqlalchemy import select

from app.jwt_handler import verify_token, token_required
from .shell import Shell, Pastbin, Forum
from DB import get_db_session
from DB.models import Shell as ShellModel, ShellCommandLog


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
    log_entries = []
    user_data = g.user_data
    user_id = user_data["user_id"]

    # on boucle sur l'ensemble des shell ou l'on veux executer la commade
    for shell_name in shell_user:
        shell_instance = instances[shell_name]
        try:
            output = shell_instance.execute(command)
        except Exception as e:
            output = f"Erreur: {str(e)}"

        # Transforme les sauts de ligne en <br> pour un affichage HTML correct
        raw_output = output
        output = raw_output.replace('\n', '<br>')

        results[shell_name] = output
        log_entries.append((shell_name, raw_output))

    if log_entries:
        try:
            with get_db_session() as session:
                for shell_name, raw_output in log_entries:
                    shell_row = session.execute(
                        select(ShellModel).where(
                            ShellModel.id_proprietaire == user_id,
                            ShellModel.nom == shell_name,
                        )
                    ).scalar_one_or_none()
                    session.add(
                        ShellCommandLog(
                            shell_id=shell_row.id if shell_row else None,
                            id_proprietaire=user_id,
                            commande=command,
                            sortie=raw_output,
                        )
                    )
        except Exception as exc:
            print(f"Erreur log commandes: {exc}")

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

    with get_db_session() as session:
        rows = session.execute(
            select(ShellModel).where(ShellModel.id_proprietaire == user_id)
        ).scalars().all()

    for shell in rows:
        shells.append(
            {
                "id": shell.id,
                "id_proprietaire": shell.id_proprietaire,
                "nom": shell.nom,
                "type_shell": shell.type_shell,
            }
        )
    return jsonify(shells)


@supprimer_shell_bp.route('/supprimer_shell', methods=['POST'])
@token_required
def supprimer_shell():
    data = request.get_json()
    id = data["id"]

    user_data = g.user_data
    user_id = user_data["user_id"]


    with get_db_session() as session:
        shell_row = session.execute(
            select(ShellModel).where(
                ShellModel.id == id,
                ShellModel.id_proprietaire == user_id,
            )
        ).scalar_one_or_none()

        if shell_row is not None:
            session.delete(shell_row)
            print("supprimer ", shell_row.nom, " de la DB")

    return jsonify({"resulat": "supprimer"})


def save_shell_to_db(user_id, nom, type):
    with get_db_session() as session:
        session.add(
            ShellModel(
                id_proprietaire=user_id,
                nom=nom,
                type_shell=type,
            )
        )
