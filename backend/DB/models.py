from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from . import Base


snippet_tag_link = Table(
    "snippet_tag_link",
    Base.metadata,
    Column("snippet_id", ForeignKey("command_snippet.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("snippet_tag.id", ondelete="CASCADE"), primary_key=True),
)


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(LargeBinary(255), nullable=False)
    ville = Column(String(255), nullable=False)

    shells = relationship(
        "Shell",
        back_populates="utilisateur",
        cascade="all, delete-orphan",
    )
    command_logs = relationship(
        "ShellCommandLog",
        back_populates="utilisateur",
        cascade="all, delete-orphan",
    )
    snippets = relationship(
        "CommandSnippet",
        back_populates="utilisateur",
        cascade="all, delete-orphan",
    )
    snippet_tags = relationship(
        "SnippetTag",
        back_populates="utilisateur",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "Note",
        back_populates="utilisateur",
        cascade="all, delete-orphan",
    )
    credentials = relationship(
        "Credential",
        back_populates="utilisateur",
        cascade="all, delete-orphan",
    )


class Shell(Base):
    __tablename__ = "shell"

    id = Column(Integer, primary_key=True)
    id_proprietaire = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False, index=True)
    nom = Column(String(255), nullable=False)
    type_shell = Column(String(50), nullable=False)

    utilisateur = relationship("Utilisateur", back_populates="shells")
    command_logs = relationship("ShellCommandLog", back_populates="shell")


class ShellCommandLog(Base):
    __tablename__ = "shell_command_log"

    id = Column(Integer, primary_key=True)
    shell_id = Column(Integer, ForeignKey("shell.id", ondelete="SET NULL"), nullable=True, index=True)
    id_proprietaire = Column(
        Integer,
        ForeignKey("utilisateurs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commande = Column(Text, nullable=False)
    sortie = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)

    utilisateur = relationship("Utilisateur", back_populates="command_logs")
    shell = relationship("Shell", back_populates="command_logs")


class CommandSnippet(Base):
    __tablename__ = "command_snippet"

    id = Column(Integer, primary_key=True)
    id_proprietaire = Column(
        Integer,
        ForeignKey("utilisateurs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    titre = Column(String(255), nullable=False)
    commande = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    type_shell = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    utilisateur = relationship("Utilisateur", back_populates="snippets")
    tags = relationship("SnippetTag", secondary=snippet_tag_link, back_populates="snippets")


class SnippetTag(Base):
    __tablename__ = "snippet_tag"
    __table_args__ = (UniqueConstraint("id_proprietaire", "libelle", name="uq_snippet_tag_user"),)

    id = Column(Integer, primary_key=True)
    id_proprietaire = Column(
        Integer,
        ForeignKey("utilisateurs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    libelle = Column(String(100), nullable=False)

    utilisateur = relationship("Utilisateur", back_populates="snippet_tags")
    snippets = relationship("CommandSnippet", secondary=snippet_tag_link, back_populates="tags")


class Note(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True)
    id_proprietaire = Column(
        Integer,
        ForeignKey("utilisateurs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    titre = Column(String(255), nullable=False)
    contenu = Column(Text, nullable=False)
    contexte = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    utilisateur = relationship("Utilisateur", back_populates="notes")


class Credential(Base):
    __tablename__ = "credential"

    id = Column(Integer, primary_key=True)
    id_proprietaire = Column(
        Integer,
        ForeignKey("utilisateurs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nom = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    secret = Column(Text, nullable=False)
    type_credential = Column(String(50), nullable=True)
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, nullable=False, server_default="1")
    created_at = Column(DateTime, server_default=func.current_timestamp(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    utilisateur = relationship("Utilisateur", back_populates="credentials")
