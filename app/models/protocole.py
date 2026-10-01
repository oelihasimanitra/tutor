"""Blocs du protocole d'expérience de représentation (module D)."""
from __future__ import annotations

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class BlocProtocole(SQLModel, table=True):
    __tablename__ = "blocs_protocole"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", index=True)
    cycle: int
    notion: str
    condition: str  # V | S | C | M
    ordre: int      # position dans le carré latin
    dates: dict | None = Field(default=None, sa_column=Column(JSON))     # J0, J+2, J+4, J+7, J+9
    mesures: dict | None = Field(default=None, sa_column=Column(JSON))   # pre, T0, T2, T7, ...
    fidelite: dict | None = Field(default=None, sa_column=Column(JSON))  # fiche de fidélité (5 cases)
    statut: str = "planifie"  # planifie | en_cours | termine | exclu
