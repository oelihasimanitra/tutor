"""Gabarits d'items (contenu global) et items générés (instances)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class GabaritItem(SQLModel, table=True):
    __tablename__ = "gabarits_items"

    id: str = Field(primary_key=True)  # ex. 'ALG.EQ1.01.i1'
    competence_id: str = Field(foreign_key="competences.id")
    type: str                           # nom de la fonction génératrice
    difficulte: int
    format_reponse: str                 # entier | fraction | expression | qcm
    enonce: str
    variables: dict = Field(default_factory=dict, sa_column=Column(JSON))
    reponse: str                        # expression sympy
    methode: str | None = None          # procédure attendue (traçage, cf. P2)
    meta: dict | None = Field(default=None, sa_column=Column(JSON))


class ItemGenere(SQLModel, table=True):
    __tablename__ = "items_generes"

    id: int | None = Field(default=None, primary_key=True)
    gabarit_id: str = Field(foreign_key="gabarits_items.id")
    variables: dict = Field(default_factory=dict, sa_column=Column(JSON))
    seed: int
    enonce: str
    reponse_attendue: str
    date_generation: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
