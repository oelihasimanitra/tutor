"""Indicateurs dérivés — tous recalculables depuis les réponses brutes.

Aucun indicateur n'est stocké comme source de vérité : on le recalcule à la
demande (SPEC §3.3 et §5 : ``indicateurs`` est un état dérivé).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

from .graph import Graphe
from .status import EtatCompetence, Reponse, Statut


def taux_reussite(reponses: Iterable[Reponse]) -> float | None:
    """Taux de réussite sur un ensemble de réponses (``None`` si aucune)."""
    rs = list(reponses)
    if not rs:
        return None
    return sum(1 for r in rs if r.est_correct) / len(rs)


def taux_par_domaine(reponses: Iterable[Reponse], graphe: Graphe) -> dict[str, float | None]:
    """Taux de réussite regroupé par domaine (NUM, ALG, ...)."""
    domaine_par_noeud = {nid: n.domaine for nid, n in graphe.noeuds.items()}
    par_domaine: dict[str, list[Reponse]] = defaultdict(list)
    for r in reponses:
        d = domaine_par_noeud.get(r.competence_id)
        if d is not None:
            par_domaine[d].append(r)
    return {d: taux_reussite(rs) for d, rs in par_domaine.items()}


def progression(etats: Mapping[str, EtatCompetence], plan_noeuds: Iterable[str]) -> float:
    """Part des nœuds du plan maîtrisés (acquis ou consolidé), dans [0, 1]."""
    noeuds = list(plan_noeuds)
    if not noeuds:
        return 0.0
    maitrises = sum(
        1
        for nid in noeuds
        if nid in etats and etats[nid].statut in (Statut.ACQUIS, Statut.CONSOLIDE)
    )
    return maitrises / len(noeuds)


def calibration(reponses: Iterable[Reponse]) -> float | None:
    """Corrélation de Pearson entre confiance annoncée et réussite (-1..1).

    Mesure la « lucidité » de l'élève (module A / métacognition) : une corrélation
    proche de 1 = bonne prédiction de sa propre réussite ; proche de 0 ou négative
    = mauvaise calibration → exercices « prédis ta réussite ».
    """
    paires = [
        (float(r.confiance_annoncee), 1.0 if r.est_correct else 0.0)
        for r in reponses
        if r.confiance_annoncee is not None
    ]
    if len(paires) < 2:
        return None

    n = len(paires)
    mx = sum(x for x, _ in paires) / n
    my = sum(y for _, y in paires) / n
    cov = sum((x - mx) * (y - my) for x, y in paires)
    vx = sum((x - mx) ** 2 for x, _ in paires)
    vy = sum((y - my) ** 2 for _, y in paires)
    if vx == 0 or vy == 0:
        return None  # variance nulle : corrélation indéfinie
    return cov / (vx**0.5 * vy**0.5)


def retention(reponses_controle: Iterable[Reponse]) -> float | None:
    """Taux de réussite aux contrôles J+7 (rétention)."""
    return taux_reussite(reponses_controle)
