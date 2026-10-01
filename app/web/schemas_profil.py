"""Schémas Pydantic des routes du profil élève (entretien, journal, point d'entrée).

``champs`` et ``statuts`` restent des JSON ouverts (``dict``) : les valeurs de
champs peuvent être int, str, bool, liste ou dict (SPEC §4-A), et les statuts
sont les lettres D / M / H (SPEC §3.8). On ne fige donc pas de colonnes.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EntretienRequete(BaseModel):
    """Corps de ``POST /eleves/{eleve_id}/entretien``.

    ``reponses`` : ``{question_id: valeur brute}`` (clés = ids d'``entretien.yaml``).
    """

    reponses: dict[str, Any] = Field(default_factory=dict)
    raison: str | None = None


class ProfilOut(BaseModel):
    """Version courante d'un profil (``POST /entretien`` et ``GET /profil``)."""

    version: int
    champs: dict[str, Any]
    statuts: dict[str, str]


class JournalEntreeOut(BaseModel):
    """Une ligne du journal des changements de profil."""

    champ: str
    ancienne_valeur: str | None = None
    nouvelle_valeur: str | None = None
    statut: str
    raison: str | None = None
    date: datetime


class JournalOut(BaseModel):
    """Réponse de ``GET /eleves/{eleve_id}/journal``."""

    journal: list[JournalEntreeOut]


class PointEntreeOut(BaseModel):
    """Réponse de ``GET /eleves/{eleve_id}/point-entree``."""

    point_entree: str
