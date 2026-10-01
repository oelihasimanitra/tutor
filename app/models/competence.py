"""Compétences (contenu global versionné) et prérequis (arêtes)."""
from __future__ import annotations

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Competence(SQLModel, table=True):
    __tablename__ = "competences"

    id: str = Field(primary_key=True)  # ex. 'ALG.EQ1.01'
    domaine: str                       # NUM PRO ALG GEO ESP FON STA LOG
    chapitre: str
    intitule: str
    niveau_ref: str
    difficulte: int
    type: str                          # procedure | concept | modelisation | raisonnement
    seuil_maitrise: dict | None = Field(default=None, sa_column=Column(JSON))
    erreurs_types: list | None = Field(default=None, sa_column=Column(JSON))
    meta: dict | None = Field(default=None, sa_column=Column(JSON))


class Prerequis(SQLModel, table=True):
    __tablename__ = "prerequis"

    id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(foreign_key="competences.id")  # le prérequis
    cible_id: str = Field(foreign_key="competences.id", index=True)  # le nœud qui l'exige
    type_arete: str = "dure"  # dure | faible
