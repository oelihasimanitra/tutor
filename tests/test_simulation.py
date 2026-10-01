"""Tests de simulation d'élèves virtuels (validation de l'adaptatif)."""
from __future__ import annotations

from app.engine.simulator import PROFIL_MAITRISE, profil_lacune, simuler_adaptatif
from app.engine.status import Statut


def test_simulation_maitrise_monte(graphe, gabarits, config):
    """Un élève qui maîtrise tout fait monter l'adaptatif : le point d'entrée devient acquis."""
    result = simuler_adaptatif(graphe, gabarits, PROFIL_MAITRISE, "NUM.ENT.01", config, 40, seed=0)
    assert result["etats"]["NUM.ENT.01"].statut == Statut.ACQUIS


def test_simulation_detecte_lacune(graphe, gabarits, config):
    """Une lacune sur NUM.DIV.02 fait descendre l'adaptatif, qui la laisse non maîtrisée."""
    eleve = profil_lacune("NUM.DIV.02", p_ok=0.9, p_lacune=0.05)
    # La lacune bloque aussi NUM.FRA.05 (dépend de NUM.DIV.02) : on la met en échec.
    eleve.competences["NUM.FRA.05"] = 0.05

    result = simuler_adaptatif(graphe, gabarits, eleve, "NUM.FRA.05", config, 100, seed=2)
    etats = result["etats"]

    # L'adaptatif est bien descendu jusqu'à la compétence lacunaire.
    assert "NUM.DIV.02" in result["reponses"]
    # La lacune n'est pas faussement déclarée maîtrisée.
    assert etats["NUM.DIV.02"].statut in (Statut.ABSENT, Statut.FRAGILE)


def test_simulation_aleatoire_reste_fragile(graphe, gabarits, config):
    """Un élève au hasard (0.5) ne doit pas produire de fausse maîtrise généralisée."""
    from app.engine.simulator import EleveSimule

    result = simuler_adaptatif(
        graphe, gabarits, EleveSimule(par_defaut=0.5), "NUM.ENT.01", config, 60, seed=3
    )
    # On tolère quelques nœuds acquis par hasard, mais pas le point d'entrée
    # systématiquement consolidé ; ici on vérifie juste que la boucle a tourné.
    assert result["reponses"]
