CREATE TABLE IF NOT EXISTS utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    prenom VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARBINARY(255) NOT NULL,
    ville VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS shell (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_proprietaire INT NOT NULL,
    nom VARCHAR(255) NOT NULL,
    type_shell VARCHAR(50) NOT NULL,
    CONSTRAINT fk_shell_utilisateur FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS shell_command_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shell_id INT NULL,
    id_proprietaire INT NOT NULL,
    commande TEXT NOT NULL,
    sortie TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_shell_command_user FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    CONSTRAINT fk_shell_command_shell FOREIGN KEY (shell_id) REFERENCES shell(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS command_snippet (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_proprietaire INT NOT NULL,
    titre VARCHAR(255) NOT NULL,
    commande TEXT NOT NULL,
    description TEXT NULL,
    type_shell VARCHAR(50) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_snippet_user FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS snippet_tag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_proprietaire INT NOT NULL,
    libelle VARCHAR(100) NOT NULL,
    CONSTRAINT fk_snippet_tag_user FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    UNIQUE KEY uq_snippet_tag_user (id_proprietaire, libelle)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS snippet_tag_link (
    snippet_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (snippet_id, tag_id),
    CONSTRAINT fk_snippet_tag_link_snippet FOREIGN KEY (snippet_id) REFERENCES command_snippet(id) ON DELETE CASCADE,
    CONSTRAINT fk_snippet_tag_link_tag FOREIGN KEY (tag_id) REFERENCES snippet_tag(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS note (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_proprietaire INT NOT NULL,
    titre VARCHAR(255) NOT NULL,
    contenu TEXT NOT NULL,
    contexte VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_note_user FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS credential (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_proprietaire INT NOT NULL,
    nom VARCHAR(255) NOT NULL,
    username VARCHAR(255) NULL,
    secret TEXT NOT NULL,
    type_credential VARCHAR(50) NULL,
    host VARCHAR(255) NULL,
    port INT NULL,
    note TEXT NULL,
    is_encrypted TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_credential_user FOREIGN KEY (id_proprietaire) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
