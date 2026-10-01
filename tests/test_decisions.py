"""Tests des règles de décision du module D (représentation)."""
from __future__ import annotations

from app.engine.decisions import decider_representation


def test_aucun_ecart_reste_multimodal():
    """Aucune condition ne domine d'au moins 2 items : rester multimodal."""
    blocs = [
        {"condition": "V", "t7_p": 4, "cycle": 1},
        {"condition": "S", "t7_p": 4, "cycle": 1},
        {"condition": "C", "t7_p": 3, "cycle": 1},
        {"condition": "M", "t7_p": 4, "cycle": 1},
    ]
    assert decider_representation(blocs) == "M"


def test_gagnant_replique_cycle2():
    """V domine d'au moins 2 items aux deux cycles => V (H renforcé)."""
    blocs = [
        {"condition": "V", "t7_p": 6, "cycle": 1},
        {"condition": "S", "t7_p": 3, "cycle": 1},
        {"condition": "V", "t7_p": 5, "cycle": 2},
        {"condition": "S", "t7_p": 3, "cycle": 2},
    ]
    assert decider_representation(blocs) == "V"


def test_ecart_cycle1_seulement_h_faible():
    """Écart au cycle 1 seulement => V (H faible)."""
    blocs = [
        {"condition": "V", "t7_p": 6, "cycle": 1},
        {"condition": "S", "t7_p": 3, "cycle": 1},
        {"condition": "V", "t7_p": 3, "cycle": 2},
        {"condition": "S", "t7_p": 3, "cycle": 2},
    ]
    assert decider_representation(blocs) == "V"


def test_multimodal_au_moins_aussi_bon():
    """Si M >= meilleure condition simple, on reste multimodal."""
    blocs = [
        {"condition": "V", "t7_p": 3, "cycle": 1},
        {"condition": "S", "t7_p": 2, "cycle": 1},
        {"condition": "M", "t7_p": 4, "cycle": 1},
    ]
    assert decider_representation(blocs) == "M"


def test_gagnants_contradictoires_reste_multimodal():
    """Gagnants différents aux cycles 1 et 2 : prudence => multimodal."""
    blocs = [
        {"condition": "V", "t7_p": 6, "cycle": 1},
        {"condition": "S", "t7_p": 3, "cycle": 1},
        {"condition": "S", "t7_p": 6, "cycle": 2},
        {"condition": "V", "t7_p": 3, "cycle": 2},
    ]
    assert decider_representation(blocs) == "M"
