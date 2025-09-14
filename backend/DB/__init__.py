import sqlite3
import os

db_name = "db.db"

def start_db():

    # Vérifie si le fichier existe et le supprime uniquement s'il est possible de le faire
    if os.path.exists(db_name):
        try:
            os.remove(db_name)
            print(f"{db_name} a été supprimée.")
        except PermissionError:
            print(f"Erreur : Impossible de supprimer {db_name} car il est utilisé par un autre processus.")
            return  # Arrête l'exécution de start_db pour éviter d'autres erreurs
    else:
        print(f"{db_name} n'existe pas.")

    # Crée ou ouvre le fichier de base de données
    conn = sqlite3.connect(db_name)

    # Crée un curseur pour exécuter des commandes SQL
    cursor = conn.cursor()

    # Crée une table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        ville TEXT NOT NULL
    )
    """)

    # Sauvegarde et ferme
    conn.commit()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shell
    (
        id INTEGER PRIMARY KEY,
        id_proprietaire TEXT NOT NULL,
        nom TEXT NOT NULL,
        type_shell TEXT NOT NULL,
        FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id)
    )
    """)

    conn.commit()
    conn.close()

    print("la db est crée")


def get_db_connection():
    # Cette fonction doit être appelée uniquement après que start_db ait été exécuté !
    conn = sqlite3.connect("DB/db.db")
    conn.row_factory = sqlite3.Row  # pour accéder aux colonnes par nom
    return conn


if __name__ == '__main__':
    start_db()  # Création/réinitialisation de la base de données