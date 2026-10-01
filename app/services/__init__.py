"""Services : le pont entre le moteur (pur) et la persistance (SQLModel).

Le moteur ne connaît ni la BDD ni HTTP. Ces services orchestrent les deux mondes
pour la phase 1 (outil tuteur).
"""
from .importer import importer_contenu
from .tuteur import TuteurService

__all__ = ["importer_contenu", "TuteurService"]
