"""Schémas Pydantic des routes de saisie tuteur (contrat HTTP, phase 1).

Ces schémas définissent le contrat d'échange avec le client. Point de sécurité
important : ``ProchainItemOut`` **ne contient jamais** ``reponse_attendue`` — la
réponse n'est exposée qu'après la saisie, dans ``ReponseOut`` (« enregistrer
réponse »), pour le feedback du tuteur.
"""
from __future__ import annotations

from pydantic import BaseModel


class EleveCreation(BaseModel):
    """Corps de ``POST /eleves``."""

    pseudonyme: str


class EleveOut(BaseModel):
    """Réponse de ``POST /eleves``."""

    id: int
    pseudonyme: str


class ProchainItemRequete(BaseModel):
    """Corps de ``POST /eleves/{eleve_id}/items/prochain``."""

    point_entree: str
    preferer_facile: bool = False


class ProchainItemOut(BaseModel):
    """Réponse d'un item à poser — SANS la réponse attendue (sécurité)."""

    item_id: int
    enonce: str
    competence_id: str
    gabarit_id: str


class ReponseSaisie(BaseModel):
    """Corps de ``POST /eleves/{eleve_id}/reponses`` (saisie par le tuteur)."""

    item_id: int
    reponse_eleve: str
    confiance_annoncee: int | None = None
    type_erreur: str | None = None
    methode_observee: str | None = None


class ReponseOut(BaseModel):
    """Réponse d'une saisie : verdict + réponse attendue (feedback tuteur)."""

    id: int
    est_correct: bool
    reponse_attendue: str


class CompetenceOut(BaseModel):
    """État dérivé d'une compétence (enums sérialisés en ``.value``)."""

    statut: str
    origine: str
    nb_reussites: int
    nb_tentatives: int


class CarteCompetencesOut(BaseModel):
    """Réponse de ``GET /eleves/{eleve_id}/competences``."""

    competences: dict[str, CompetenceOut]
