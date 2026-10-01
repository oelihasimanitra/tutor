"""Initialisation de la base pour l'application web (engine + tables)."""
from __future__ import annotations

import os
from pathlib import Path

import app.models  # noqa: F401  (enregistre les tables dans SQLModel.metadata)
from app.models import create_db_and_tables, create_engine_sqlite

# Chemin de la base : absolu (racine du projet), jamais relatif au dossier de
# lancement. Surchargeable via la variable d'environnement TUTORAT_DB_URL.
ROOT = Path(__file__).resolve().parent.parent.parent
DATABASE_URL = os.environ.get("TUTORAT_DB_URL", f"sqlite:///{(ROOT / 'tutorat.db').as_posix()}")

# Engine partagé de l'application. SQLite local, jamais versionné (cf. .gitignore).
engine = create_engine_sqlite(DATABASE_URL)


def init_db() -> None:
    """Crée les tables au démarrage (idempotent, via ``create_all``).

    Conservé pour les contextes de test ; en production on préfère :func:`migrer`.
    """
    create_db_and_tables(engine)


def migrer() -> None:
    """Applique les migrations Alembic (remplace ``create_all`` en production)."""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / "alembic.ini"))
    command.upgrade(cfg, "head")
