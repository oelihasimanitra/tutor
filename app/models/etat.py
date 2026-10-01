"""État dérivé d'une compétence pour un élève (recalculable)."""
from __future__ import annotations

from datetime import date

from sqlmodel import Field, SQLModel


class EtatCompetence(SQLModel, table=True):
    __tablename__ = "etat_competence"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", index=True)
    competence_id: str = Field(foreign_key="competences.id")
    statut: str        # absent | fragile | acquis | consolide
    origine: str       # mesure | propagation | controle
    nb_reussites: int = 0
    nb_tentatives: int = 0
    derniere_date: date | None = None
    date_acquisition: date | None = None
    date_consolidation: date | None = None
