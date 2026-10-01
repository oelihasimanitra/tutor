"""Plan de progression et indicateurs dérivés."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Plan(SQLModel, table=True):
    __tablename__ = "plan"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", index=True)
    version: int
    date_creation: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cible_noeuds: list = Field(default_factory=list, sa_column=Column(JSON))     # nœuds cibles
    noeuds_ordonnes: list = Field(default_factory=list, sa_column=Column(JSON))  # ordre de travail
    echeances: dict | None = Field(default=None, sa_column=Column(JSON))         # {noeud: date}
    statut: str = "actif"  # actif | archive


class Indicateur(SQLModel, table=True):
    __tablename__ = "indicateurs"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", index=True)
    nom: str  # ex. 'taux_reussite_NUM'
    valeur: dict = Field(default_factory=dict, sa_column=Column(JSON))
    periode: str = "global"  # 7j | 30j | global
    date_calcul: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
