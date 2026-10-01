"""Base de données : engine SQLite + création des tables."""
from __future__ import annotations

from sqlmodel import SQLModel, create_engine


def create_engine_sqlite(url: str = "sqlite:///tutorat.db"):
    """Crée un engine SQLite.

    ``url`` par défaut pointe vers un fichier local (jamais versionné, cf.
    .gitignore). Pour les tests on passe ``sqlite://`` (en mémoire).
    """
    return create_engine(url, echo=False)


def create_db_and_tables(engine) -> None:
    """Crée toutes les tables enregistrées dans ``SQLModel.metadata``.

    Nécessite d'avoir importé ``app.models`` au préalable (sinon les tables ne
    sont pas enregistrées). Idempotent : ``create_all`` ignore les tables déjà
    existantes.
    """
    SQLModel.metadata.create_all(engine)
