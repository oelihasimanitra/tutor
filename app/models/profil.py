"""Profil élève versionné + journal des changements.

Le profil est « vivant » (SPEC §4) : chaque modification crée une **nouvelle
version** et journalise champ par champ (ancienne/nouvelle valeur, statut D/M/H,
raison). ``champs`` et ``statuts`` sont des JSON pour rester extensibles sans
figer des dizaines de colonnes.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Profil(SQLModel, table=True):
    __tablename__ = "profils"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", index=True)
    version: int
    date_version: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raison: str | None = None
    champs: dict = Field(default_factory=dict, sa_column=Column(JSON))   # {champ: valeur}
    statuts: dict = Field(default_factory=dict, sa_column=Column(JSON))  # {champ: D|M|H}


class JournalProfil(SQLModel, table=True):
    __tablename__ = "journal_profil"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", index=True)
    version: int
    champ: str
    ancienne_valeur: str | None = None
    nouvelle_valeur: str | None = None
    statut: str  # D | M | H
    raison: str | None = None
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
