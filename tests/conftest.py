"""Fixtures et helpers partagés des tests.

On charge le contenu **réel** (graphe + gabarits) et la config **réelle** pour
tester le système en conditions proches de l'usage, pas sur des données bricolées.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.engine.config import load_config
from app.engine.content import charger_contenu
from app.engine.graph import Graphe, Noeud
from app.engine.items import Gabarit

ROOT = Path(__file__).resolve().parent.parent
GRAPH_PATH = ROOT / "app" / "content" / "graph" / "num_alg.yaml"
ITEMS_PATHS = [
    ROOT / "app" / "content" / "items" / "num.yaml",
    ROOT / "app" / "content" / "items" / "alg.yaml",
]


@pytest.fixture(scope="session")
def config():
    """Config réelle depuis app/config/default.yaml."""
    return load_config()


@pytest.fixture(scope="session")
def contenu():
    """(graphe, gabarits) chargés depuis le contenu réel, avec validation croisée."""
    return charger_contenu(GRAPH_PATH, ITEMS_PATHS)


@pytest.fixture(scope="session")
def graphe(contenu):
    return contenu[0]


@pytest.fixture(scope="session")
def gabarits(contenu):
    return contenu[1]


# --- Helpers (fixtures factory) pour des structures minimales --------------

@pytest.fixture
def make_noeud():
    """Factory : construit un nœud minimal pour des graphes de test."""
    def _make(node_id: str, prerequis=(), items=(), domaine="NUM", difficulte=1) -> Noeud:
        return Noeud(
            id=node_id,
            domaine=domaine,
            chapitre="test",
            intitule=f"nœud {node_id}",
            niveau_ref="5e",
            difficulte=difficulte,
            type="procedure",
            prerequis=tuple(prerequis),
            items=tuple(items),
        )
    return _make


@pytest.fixture
def make_gabarit():
    """Factory : construit un gabarit minimal dont la réponse est connue."""
    def _make(gabarit_id: str, competence_id: str = "C", reponse: str = "1") -> Gabarit:
        return Gabarit(
            id=gabarit_id,
            competence_id=competence_id,
            type="test",
            difficulte=1,
            format_reponse="entier",
            enonce="question ?",
            variables={},
            reponse=reponse,
        )
    return _make
