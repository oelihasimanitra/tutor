"""Tests des statuts de compétence et de la propagation des prérequis."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.engine.graph import Graphe
from app.engine.status import (
    EtatCompetence,
    Origine,
    Reponse,
    Statut,
    calculer_etats,
    consolider,
    statut_noeud,
)

D = datetime(2026, 1, 1)


def _reponses(corrects, jour=0, methode=None):
    """Construit une liste de réponses datées successives (1/jour)."""
    return [
        Reponse(
            competence_id="N",
            est_correct=ok,
            date=D + timedelta(days=jour + i),
            methode_observee=methode,
        )
        for i, ok in enumerate(corrects)
    ]


def test_acquis_seuil_atteint(config):
    """3 réussites sur 4 (fenêtre) => acquis, origine mesure."""
    etat = statut_noeud(_reponses([True, True, True, False]), config)
    assert etat.statut == Statut.ACQUIS
    assert etat.origine == Origine.MESURE


def test_fragile_seuil_non_atteint(config):
    """2 réussites sur 4 => fragile."""
    etat = statut_noeud(_reponses([True, False, True, False]), config)
    assert etat.statut == Statut.FRAGILE


def test_absent_sans_reponse(config):
    """Aucune réponse => absent."""
    assert statut_noeud([], config).statut == Statut.ABSENT


def test_methode_incorrecte_non_comptee(config):
    """Avec methode_correcte actif, une réussite à mauvaise méthode ne compte pas."""
    reponses = _reponses([True, True, True], methode="mauvaise")
    etat = statut_noeud(reponses, config, methode_attendue="bonne")
    assert etat.statut == Statut.FRAGILE  # tentatives présentes mais aucune réussite valide
    assert etat.nb_reussites == 0


def test_fenetre_glissante(config):
    """On ne regarde que les 4 dernières tentatives : un vieil échec est ignoré."""
    reponses = [
        Reponse("N", False, D),
        Reponse("N", True, D + timedelta(days=1)),
        Reponse("N", True, D + timedelta(days=2)),
        Reponse("N", True, D + timedelta(days=3)),
        Reponse("N", True, D + timedelta(days=4)),
    ]
    etat = statut_noeud(reponses, config)
    assert etat.statut == Statut.ACQUIS


def test_consolidation_j7(config):
    """Acquis + contrôle réussi à J+7 => consolide."""
    reponses = _reponses([True, True, True])
    etat = statut_noeud(reponses, config)
    assert etat.statut == Statut.ACQUIS
    controle = Reponse("N", True, etat.date_acquisition + timedelta(days=7))
    etat = consolider(etat, reponses + [controle], config)
    assert etat.statut == Statut.CONSOLIDE
    assert etat.origine == Origine.CONTROLE


def test_consolidation_trop_tot(config):
    """Un contrôle réussi avant J+7 ne consolide pas."""
    reponses = _reponses([True, True, True])
    etat = statut_noeud(reponses, config)
    controle = Reponse("N", True, etat.date_acquisition + timedelta(days=6))
    etat = consolider(etat, reponses + [controle], config)
    assert etat.statut == Statut.ACQUIS


def test_propagation_prerequis(config, make_noeud):
    """B maîtrisé (mesure) => son prérequis A est présumé acquis (propagation)."""
    graphe = Graphe(noeuds={
        "A": make_noeud("A"),
        "B": make_noeud("B", prerequis=("A",)),
    })
    reponses = {"B": _reponses([True, True, True])}
    etats = calculer_etats(graphe, reponses, config)
    assert etats["B"].statut == Statut.ACQUIS
    assert etats["B"].origine == Origine.MESURE
    assert etats["A"].statut == Statut.ACQUIS
    assert etats["A"].origine == Origine.PROPAGATION


def test_mesure_emporte_sur_propagation(config, make_noeud):
    """Un prérequis mesuré fragile reste fragile malgré la propagation depuis B."""
    graphe = Graphe(noeuds={
        "A": make_noeud("A"),
        "B": make_noeud("B", prerequis=("A",)),
    })
    reponses = {
        "A": _reponses([True, False, False, False]),  # fragile (mesure)
        "B": _reponses([True, True, True]),           # acquis (mesure)
    }
    etats = calculer_etats(graphe, reponses, config)
    assert etats["B"].statut == Statut.ACQUIS
    assert etats["A"].statut == Statut.FRAGILE
    assert etats["A"].origine == Origine.MESURE


def test_date_acquisition_figee_au_premier_franchissement(config):
    """Régression : la date d'acquisition ne dérive pas avec la fenêtre glissante."""
    reponses = [
        Reponse("N", True, D),
        Reponse("N", True, D + timedelta(hours=1)),
        Reponse("N", False, D + timedelta(hours=2)),
        Reponse("N", True, D + timedelta(hours=3)),   # 3e réussite -> acquis
        Reponse("N", True, D + timedelta(days=8)),     # contrôle tardif
    ]
    etat = statut_noeud(reponses, config)
    # Figée au premier franchissement (3e réussite), pas au contrôle J+8.
    assert etat.date_acquisition == D + timedelta(hours=3)


def test_echec_apres_acquisition_retour_fragile(config):
    """Un échec récent fait retomber à fragile, sans effacer date_acquisition."""
    reponses = [
        Reponse("N", True, D),
        Reponse("N", True, D + timedelta(hours=1)),
        Reponse("N", True, D + timedelta(hours=2)),   # acquis
        Reponse("N", False, D + timedelta(days=1)),
        Reponse("N", False, D + timedelta(days=2)),
        Reponse("N", False, D + timedelta(days=3)),
        Reponse("N", False, D + timedelta(days=4)),   # fenêtre = 4 échecs
    ]
    etat = statut_noeud(reponses, config)
    assert etat.statut == Statut.FRAGILE
    assert etat.date_acquisition == D + timedelta(hours=2)  # figé


def test_ordre_meme_jour_par_horodatage(config):
    """Des réponses le même jour sont ordonnées par horodatage (heure)."""
    reponses = [
        Reponse("N", False, D),
        Reponse("N", True, D + timedelta(hours=1)),
        Reponse("N", True, D + timedelta(hours=2)),
        Reponse("N", True, D + timedelta(hours=3)),
    ]
    etat = statut_noeud(reponses, config)
    assert etat.statut == Statut.ACQUIS  # 3 réussites sur les 4 dernières
