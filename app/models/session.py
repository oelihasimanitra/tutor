"""Sessions, réponses (événements bruts) et observations.

``reponses`` est la table centrale du principe « événements bruts, état dérivé »
(SPEC §3.3) : on n'y stocke que des faits, jamais modifiés ; tout le reste se
recalcule.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", index=True)
    date_debut: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    date_fin: datetime | None = None
    type: str  # entretien | test_adaptatif | seance | protocole_D
    notes: str | None = None


class Reponse(SQLModel, table=True):
    __tablename__ = "reponses"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", index=True)
    session_id: int | None = Field(default=None, foreign_key="sessions.id")
    item_id: int | None = Field(default=None, foreign_key="items_generes.id")
    competence_id: str | None = Field(default=None, foreign_key="competences.id")
    reponse_eleve: str | None = None        # brute, telle que saisie
    est_correct: bool | None = None         # verdict immédiat (recalculable via item)
    temps_reponse_ms: int | None = None
    confiance_annoncee: int | None = None   # 1..5
    type_erreur: str | None = None          # etourderie | procedure | concept | lacune
    methode_observee: str | None = None     # traçage de méthode (P2)
    est_controle: bool = False              # item de contrôle (prérequis propagé)
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Observation(SQLModel, table=True):
    __tablename__ = "observations"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", index=True)
    session_id: int | None = Field(default=None, foreign_key="sessions.id")
    type: str  # latence, abandon, autocorrection, demande_indice, ...
    valeur: dict | None = Field(default=None, sa_column=Column(JSON))
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
