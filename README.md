# Centre de controle C2

Tableau de bord de command and control construit autour dune API Flask, dune interface Vue 3 et dune base SQLite legere. Le backend fournit lautentification, la gestion des listeners et lexecution de commandes tandis que le frontend offre un UI unifie pour piloter les agents et visualiser les retours en direct.

## Structure du projet

```
.
├── backend/           # Application Flask, JWT, acces SQLite
├── frontend/          # Application Vue 3 + Vite
├── charge_utile/      # Outils annexes (relay forum, etc.)
├── requirements.txt   # Dependances Python globales
└── README.md
```

## Fonctionnalites

- Authentification JWT avec inscription et connexion stockees dans SQLite.
- Gestion de listeners reverse shell, Pastebin et forum.
- Terminal multi-shell pour diffuser une commande vers plusieurs cibles.
- Dashboard obscur concu pour lanalyse temps reel.
- Integrations externes configurees via les fichiers `.env`.

## Prerequis

- Python 3.11 ou plus (teste avec 3.12)
- Node.js 18 ou plus
- npm (fourni avec Node)

## Mise en place du backend

1. Creer lenvironnement virtuel et installer les dependances :
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Windows : .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
2. Configurer les variables denvironnement. Exemple de `.env` :
   ```env
   SECRET_KEY=a-remplacer
   JWT_EXPIRATION_DELTA=3600
   API_KEY=cle-pastebin
   USER_PAST=utilisateur-pastebin
   PASSWORD=motdepasse-pastebin
   ```
   `API_KEY`, `USER_PAST` et `PASSWORD` sont requis si vous activez le listener Pastebin.
3. Initialiser la base SQLite (cree `DB/db.db`) :
   ```bash
   python -m DB
   ```
4. Lancer lAPI :
   ```bash
   python app.py
   ```
   Par defaut le service ecoute sur `http://127.0.0.1:5000`.

## Mise en place du frontend

1. Installer les dependances et demarrer Vite :
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Verifier `frontend/.env` pour pointer vers lAPI Flask :
   ```env
   VITE_API_URL=http://127.0.0.1:5000
   ```
3. Ouvrir lURL fournie par Vite (souvent `http://localhost:5173`). Pour un build de production utiliser `npm run build`.

## Endpoints principaux

| Methode | Chemin                              | Description                               |
|---------|-------------------------------------|-------------------------------------------|
| GET     | `/api/test`                         | Test rapide de connectivite.              |
| POST    | `/auth/signup`                      | Creation dun nouvel utilisateur.          |
| POST    | `/auth/signin`                      | Authentification et retour du JWT.        |
| GET     | `/api/check-token`                  | Verification dun token existant.          |
| POST    | `/dashboard/listener`               | Enregistrement dun listener.              |
| POST    | `/dashboard/terminal`               | Execution dune commande sur des shells.   |
| GET     | `/dashboard/shells_list`            | Liste des shells rattaches a lutilisateur.|
| POST    | `/dashboard/supprimer_shell`        | Suppression dun shell.                    |

Toutes les routes `/dashboard/*` exigent len-tete `Authorization: Bearer <token>`.

## Schema de base de donnees

`backend/DB/__init__.py` cree deux tables :

- `utilisateurs` : `id`, `nom`, `prenom`, `username`, `email`, `password`, `ville`.
- `shell` : `id`, `id_proprietaire`, `nom`, `type_shell` (cle etrangere vers `utilisateurs.id`).

Les mots de passe sont stockes en hash bcrypt et les tokens sont signes en HS256.

## Conseils de developpement

- Regenerer `backend/requirements.txt` avec `pip freeze > requirements.txt` apres toute nouvelle dependance.
- Les variables de style globales sont dans `frontend/src/style.css`; les vues gardent leurs styles scopes.
- S'assurer que les ports des reverse shells sont accessibles (binding sur `0.0.0.0`).
- Ne pas versionner les fichiers `.env`; conserver les secrets en dehors du depot.

## Licence

Ce projet nest pas livre avec une licence. Ajoutez-en une avant diffusion publique.
