"""Initialisation de la base pour l'application web (engine + tables)."""
from __future__ import annotations

import app.models  # noqa: F401  (enregistre les tables dans SQLModel.metadata)
from app.models import create_db_and_tables, create_engine_sqlite

# Engine partagé de l'application. SQLite local, jamais versionné (cf. .gitignore).
engine = create_engine_sqlite("sqlite:///tutorat.db")


def init_db() -> None:
    """Crée les tables au démarrage (idempotent)."""
    create_db_and_tables(engine)
