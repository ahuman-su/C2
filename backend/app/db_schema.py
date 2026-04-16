from DB import get_db_connection


_dashboard_schema_ready = False

UNUSED_COLUMNS = {
    "command_snippet": ("description",),
    "note": ("contexte",),
    "credential": ("type_credential", "host", "port", "note"),
}

TABLE_DEFINITIONS = (
    """
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nom VARCHAR(255) NOT NULL,
        prenom VARCHAR(255) NOT NULL,
        username VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        password VARBINARY(255) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS shell (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_proprietaire INT NOT NULL,
        nom VARCHAR(255) NOT NULL,
        type_shell VARCHAR(50) NOT NULL,
        CONSTRAINT fk_shell_utilisateur FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS shell_command_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        shell_id INT NOT NULL,
        id_proprietaire INT NOT NULL,
        commande TEXT NOT NULL,
        sortie TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_shell_command_log_shell FOREIGN KEY (shell_id) REFERENCES shell(id) ON DELETE CASCADE,
        CONSTRAINT fk_shell_command_log_utilisateur FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS shell_machine_info (
        id INT AUTO_INCREMENT PRIMARY KEY,
        shell_id INT NOT NULL,
        id_proprietaire INT NOT NULL,
        id_output TEXT NOT NULL,
        groups_output TEXT NOT NULL,
        users_output TEXT NOT NULL,
        uname_output TEXT NOT NULL,
        raw_payload LONGTEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_shell_machine_info_shell FOREIGN KEY (shell_id) REFERENCES shell(id) ON DELETE CASCADE,
        CONSTRAINT fk_shell_machine_info_utilisateur FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE,
        CONSTRAINT uq_shell_machine_info_shell UNIQUE (shell_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS command_snippet (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_proprietaire INT NOT NULL,
        titre VARCHAR(255) NOT NULL,
        commande TEXT NOT NULL,
        type_shell VARCHAR(50) DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_command_snippet_utilisateur FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS note (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_proprietaire INT NOT NULL,
        titre VARCHAR(255) NOT NULL,
        contenu TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_note_utilisateur FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS credential (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_proprietaire INT NOT NULL,
        nom VARCHAR(255) NOT NULL,
        username VARCHAR(255) DEFAULT '',
        secret TEXT NOT NULL,
        is_encrypted TINYINT(1) NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_credential_utilisateur FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS snippet_tag (
        id INT AUTO_INCREMENT PRIMARY KEY,
        id_proprietaire INT NOT NULL,
        libelle VARCHAR(100) NOT NULL,
        CONSTRAINT fk_snippet_tag_utilisateur FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE,
        CONSTRAINT uq_snippet_tag_owner_label UNIQUE (id_proprietaire, libelle)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS snippet_tag_link (
        snippet_id INT NOT NULL,
        tag_id INT NOT NULL,
        PRIMARY KEY (snippet_id, tag_id),
        CONSTRAINT fk_snippet_tag_link_snippet FOREIGN KEY (snippet_id) REFERENCES command_snippet(id) ON DELETE CASCADE,
        CONSTRAINT fk_snippet_tag_link_tag FOREIGN KEY (tag_id) REFERENCES snippet_tag(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
)

LEGACY_MIGRATIONS = (
    {
        "legacy_table": "snippets",
        "target_table": "command_snippet",
        "copy_sql": """
            INSERT INTO command_snippet (
                id,
                id_proprietaire,
                titre,
                commande,
                type_shell,
                created_at,
                updated_at
            )
            SELECT
                id,
                id_proprietaire,
                titre,
                contenu,
                langage,
                created_at,
                created_at
            FROM snippets
        """,
    },
    {
        "legacy_table": "notes",
        "target_table": "note",
        "copy_sql": """
            INSERT INTO note (
                id,
                id_proprietaire,
                titre,
                contenu,
                created_at,
                updated_at
            )
            SELECT
                id,
                id_proprietaire,
                titre,
                contenu,
                created_at,
                created_at
            FROM notes
        """,
    },
    {
        "legacy_table": "password_entries",
        "target_table": "credential",
        "copy_sql": """
            INSERT INTO credential (
                id,
                id_proprietaire,
                nom,
                username,
                secret,
                is_encrypted,
                created_at,
                updated_at
            )
            SELECT
                id,
                id_proprietaire,
                libelle,
                identifiant,
                mot_de_passe,
                0,
                created_at,
                created_at
            FROM password_entries
        """,
    },
)


def _table_exists(cursor, table_name):
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None


def _table_is_empty(cursor, table_name):
    cursor.execute(f"SELECT COUNT(*) AS total FROM {table_name}")
    row = cursor.fetchone()
    return not row or row["total"] == 0


def _table_row_count(cursor, table_name):
    cursor.execute(f"SELECT COUNT(*) AS total FROM {table_name}")
    row = cursor.fetchone()
    return 0 if not row else row["total"]


def _column_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND column_name = %s
        """,
        (table_name, column_name),
    )
    return cursor.fetchone() is not None


def _migrate_legacy_tables(cursor):
    for migration in LEGACY_MIGRATIONS:
        if not _table_exists(cursor, migration["legacy_table"]):
            continue
        if not _table_exists(cursor, migration["target_table"]):
            continue
        if not _table_is_empty(cursor, migration["target_table"]):
            legacy_count = _table_row_count(cursor, migration["legacy_table"])
            target_count = _table_row_count(cursor, migration["target_table"])
            if target_count >= legacy_count:
                cursor.execute(f"DROP TABLE {migration['legacy_table']}")
            continue

        cursor.execute(migration["copy_sql"])

        legacy_count = _table_row_count(cursor, migration["legacy_table"])
        target_count = _table_row_count(cursor, migration["target_table"])
        if target_count >= legacy_count:
            cursor.execute(f"DROP TABLE {migration['legacy_table']}")


def _drop_unused_columns(cursor):
    for table_name, column_names in UNUSED_COLUMNS.items():
        if not _table_exists(cursor, table_name):
            continue
        for column_name in column_names:
            if not _column_exists(cursor, table_name, column_name):
                continue
            cursor.execute(
                f"ALTER TABLE `{table_name}` DROP COLUMN `{column_name}`"
            )


def ensure_dashboard_tables():
    global _dashboard_schema_ready
    if _dashboard_schema_ready:
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for statement in TABLE_DEFINITIONS:
            cursor.execute(statement)
        _migrate_legacy_tables(cursor)
        _drop_unused_columns(cursor)
        conn.commit()
        _dashboard_schema_ready = True
    finally:
        conn.close()
