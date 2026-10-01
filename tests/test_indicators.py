"""Tests des indicateurs dérivés."""
from __future__ import annotations

from datetime import date

import pytest

from app.engine.indicators import calibration, progression, taux_par_domaine, taux_reussite
from app.engine.status import EtatCompetence, Origine, Reponse, Statut

D = date(2026, 1, 1)


def test_taux_reussite():
    rs = [Reponse("n", True, D), Reponse("n", False, D), Reponse("n", True, D)]
    assert taux_reussite(rs) == pytest.approx(2 / 3)
    assert taux_reussite([]) is None


def test_taux_par_domaine(graphe):
    rs = [
        Reponse("NUM.ENT.01", True, D),
        Reponse("NUM.ENT.01", False, D),
        Reponse("ALG.LIT.01", True, D),
    ]
    taux = taux_par_domaine(rs, graphe)
    assert taux["NUM"] == pytest.approx(0.5)
    assert taux["ALG"] == pytest.approx(1.0)


def test_progression(graphe):
    etats = {
        "A": EtatCompetence(statut=Statut.ACQUIS, origine=Origine.MESURE),
        "B": EtatCompetence(statut=Statut.FRAGILE),
        "C": EtatCompetence(statut=Statut.ABSENT),
    }
    assert progression(etats, ["A", "B", "C"]) == pytest.approx(1 / 3)
    assert progression(etats, []) == 0.0


def test_calibration_positive():
    """Confiance haute => réussite, basse => échec : corrélation parfaite (+1.0)."""
    rs = [
        Reponse("n", False, D, confiance_annoncee=1),
        Reponse("n", True, D, confiance_annoncee=5),
    ]
    assert calibration(rs) == pytest.approx(1.0)


def test_calibration_negative():
    """Confiance inversée : corrélation parfaite négative (-1.0)."""
    rs = [
        Reponse("n", True, D, confiance_annoncee=1),
        Reponse("n", False, D, confiance_annoncee=5),
    ]
    assert calibration(rs) == pytest.approx(-1.0)


def test_calibration_sans_confiance():
    """Sans confiance annoncée, la calibration est indéfinie (None)."""
    rs = [Reponse("n", True, D), Reponse("n", False, D)]
    assert calibration(rs) is None


def test_calibration_variance_nulle():
    """Une confiance constante rend la corrélation indéfinie (None)."""
    rs = [Reponse("n", True, D, confiance_annoncee=3), Reponse("n", False, D, confiance_annoncee=3)]
    assert calibration(rs) is None
