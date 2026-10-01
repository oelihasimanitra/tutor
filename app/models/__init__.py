"""Schéma de données SQLModel (miroir du DDL du livrable 2).

Importer ce package enregistre tous les modèles dans ``SQLModel.metadata`` —
indispensable avant ``create_db_and_tables``.
"""
from .base import create_db_and_tables, create_engine_sqlite
from .competence import Competence, Prerequis
from .eleve import Eleve, Identite
from .etat import EtatCompetence
from .item import GabaritItem, ItemGenere
from .plan import Indicateur, Plan
from .profil import JournalProfil, Profil
from .protocole import BlocProtocole
from .session import Observation, Reponse, Session

__all__ = [
    "create_db_and_tables",
    "create_engine_sqlite",
    "Competence",
    "Prerequis",
    "Eleve",
    "Identite",
    "EtatCompetence",
    "GabaritItem",
    "ItemGenere",
    "Indicateur",
    "Plan",
    "JournalProfil",
    "Profil",
    "BlocProtocole",
    "Observation",
    "Reponse",
    "Session",
]
