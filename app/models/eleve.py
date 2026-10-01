"""Élèves (pseudonyme) et identités (table séparée, données sensibles).

Séparation RGPD (SPEC §3.10) : l'identité réelle ne vit que dans ``identites``,
jamais dans ``eleves`` qui ne porte qu'un pseudonyme.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel


class Eleve(SQLModel, table=True):
    __tablename__ = "eleves"

    id: int | None = Field(default=None, primary_key=True)
    pseudonyme: str = Field(unique=True, index=True)
    statut: str = "actif"  # actif | archive | supprime (suppression à la demande)
    date_creation: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Identite(SQLModel, table=True):
    __tablename__ = "identites"

    id: int | None = Field(default=None, primary_key=True)
    eleve_id: int = Field(foreign_key="eleves.id", unique=True)
    nom: str | None = None
    prenom: str | None = None
    date_naissance: date | None = None
    contact_famille: str | None = None
    consentement: bool = False
    date_consentement: date | None = None
