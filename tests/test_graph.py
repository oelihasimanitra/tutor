"""Tests du graphe : chargement, navigation, validation d'acyclicité."""
from __future__ import annotations

import pytest

from app.engine.graph import Graphe, GrapheCycleError, Noeud


def test_chargement_graphe_reel(graphe):
    """Le graphe réel doit couvrir le périmètre NUM + ALG (SPEC : 80-120 nœuds)."""
    assert len(graphe) >= 80
    assert "ALG.EQ1.03" in graphe
    assert "NUM.FRA.04" in graphe
    assert graphe["NUM.FRA.04"].domaine == "NUM"
    assert graphe["ALG.EQ1.03"].domaine == "ALG"


def test_ordre_topologique_respecte_prerequis(graphe):
    """Dans le tri topologique, tout prérequis précède son dépendant."""
    ordre = graphe.ordre_topologique()
    position = {nid: i for i, nid in enumerate(ordre)}
    for nid in graphe.ids():
        for pre in graphe.prerequis(nid):
            assert position[pre] < position[nid]


def test_successeurs(graphe):
    """NUM.DIV.01 est prérequis de NUM.DIV.02 et NUM.FRA.01."""
    assert set(graphe.successeurs("NUM.DIV.01")) >= {"NUM.DIV.02", "NUM.FRA.01"}


def test_cycle_rejete():
    """Un cycle (A prérequis de B, B prérequis de A) doit être rejeté."""
    a = Noeud("A", "NUM", "t", "a", "5e", 1, "procedure", prerequis=("B",))
    b = Noeud("B", "NUM", "t", "b", "5e", 1, "procedure", prerequis=("A",))
    g = Graphe(noeuds={"A": a, "B": b})
    with pytest.raises(GrapheCycleError):
        g.valider()


def test_prerequis_inconnu_rejete():
    """Un prérequis pointant vers un nœud inexistant est rejeté au chargement."""
    a = Noeud("A", "NUM", "t", "a", "5e", 1, "procedure", prerequis=("INCONNU",))
    g = Graphe(noeuds={"A": a})
    with pytest.raises(KeyError):
        g.valider()


def test_graphe_sans_cycle_est_valide():
    """Un graphe acyclique passe la validation sans erreur."""
    a = Noeud("A", "NUM", "t", "a", "5e", 1, "procedure", prerequis=())
    b = Noeud("B", "NUM", "t", "b", "5e", 1, "procedure", prerequis=("A",))
    g = Graphe(noeuds={"A": a, "B": b})
    assert g.ordre_topologique() == ["A", "B"]


def test_chaque_noeud_a_variante_de_difficulte(graphe, gabarits):
    """Chaque nœud doit avoir >= 2 gabarits de difficultés différentes (preferer_facile)."""
    sans_variante = []
    for nid in graphe.ids():
        ids = graphe[nid].items
        difficultes = {gabarits[i].difficulte for i in ids if i in gabarits}
        if len(difficultes) < 2:
            sans_variante.append(nid)
    assert not sans_variante, f"nœuds sans variante de difficulté : {sans_variante}"
