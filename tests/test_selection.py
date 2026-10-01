"""Tests de la sélection adaptative du prochain item."""
from __future__ import annotations

from app.engine.graph import Graphe
from app.engine.selection import prochain_item
from app.engine.status import EtatCompetence, Origine, Statut


def _chaine(make_noeud, make_gabarit):
    """Mini graphe linéaire A -> B -> C avec un gabarit par nœud."""
    graphe = Graphe(noeuds={
        "A": make_noeud("A", items=("ia",)),
        "B": make_noeud("B", prerequis=("A",), items=("ib",)),
        "C": make_noeud("C", prerequis=("B",), items=("ic",)),
    })
    gabarits = {
        "ia": make_gabarit("ia", competence_id="A"),
        "ib": make_gabarit("ib", competence_id="B"),
        "ic": make_gabarit("ic", competence_id="C"),
    }
    return graphe, gabarits


def test_attaque_noeud_sans_prerequis(graphe, gabarits):
    """Un nœud sans prérequis non maîtrisé : on pose un item dessus."""
    etats = {nid: EtatCompetence() for nid in graphe.ids()}
    item = prochain_item(graphe, etats, gabarits, "NUM.ENT.01")
    assert item is not None
    assert item.competence_id == "NUM.ENT.01"


def test_monte_apres_acquisition(graphe, gabarits):
    """Nœud maîtrisé : on monte vers son successeur non maîtrisé."""
    etats = {nid: EtatCompetence() for nid in graphe.ids()}
    etats["NUM.ENT.01"] = EtatCompetence(statut=Statut.ACQUIS, origine=Origine.MESURE)
    item = prochain_item(graphe, etats, gabarits, "NUM.ENT.01")
    assert item is not None
    assert item.competence_id == "NUM.ENT.02"  # successeur direct


def test_descend_vers_prerequis(make_noeud, make_gabarit):
    """Nœud non maîtrisé avec prérequis non maîtrisé : on descend vers le prérequis."""
    graphe, gabarits = _chaine(make_noeud, make_gabarit)
    etats = {nid: EtatCompetence() for nid in graphe.ids()}
    # C a pour prérequis B (non maîtrisé) -> on descend à B -> puis à A.
    item = prochain_item(graphe, etats, gabarits, "C")
    assert item is not None
    assert item.competence_id == "A"  # tout en bas de la chaîne


def test_branche_epuisee_retourne_none(make_noeud, make_gabarit):
    """Tout est maîtrisé et sans successeur : retourne None (fin de branche)."""
    graphe, gabarits = _chaine(make_noeud, make_gabarit)
    etats = {
        "A": EtatCompetence(statut=Statut.ACQUIS, origine=Origine.MESURE),
        "B": EtatCompetence(statut=Statut.ACQUIS, origine=Origine.MESURE),
        "C": EtatCompetence(statut=Statut.ACQUIS, origine=Origine.MESURE),
    }
    assert prochain_item(graphe, etats, gabarits, "C") is None


def test_noeud_sans_item_ignore(make_noeud):
    """Un nœud sans gabarit ne fait pas planter la sélection (ignoré)."""
    graphe = Graphe(noeuds={"A": make_noeud("A", items=("inexistant",))})
    etats = {"A": EtatCompetence()}
    assert prochain_item(graphe, etats, {}, "A") is None


def test_preferer_facile(graphe, gabarits):
    """preferer_facile = True restreint au gabarit de difficulté minimale du nœud."""
    etats = {nid: EtatCompetence() for nid in graphe.ids()}
    etats["NUM.ENT.01"] = EtatCompetence(statut=Statut.ACQUIS, origine=Origine.MESURE)
    etats["NUM.ENT.02"] = EtatCompetence(statut=Statut.ACQUIS, origine=Origine.MESURE)
    item = prochain_item(graphe, etats, gabarits, "NUM.ENT.02", preferer_facile=True)
    assert item is not None
    assert item.competence_id == "NUM.DIV.01"
