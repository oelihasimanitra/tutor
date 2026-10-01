"""Planificateur : chemin critique + échéances J+2 / J+7.

Le plan ordonne les nœuds à travailler (prérequis avant dépendants) pour atteindre
des nœuds cibles. Les échéances de révision sont **relatives** à la date
d'acquisition de chaque nœud, pas figées à l'avance (SPEC §4-B).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable, Mapping

from .config import Config
from .graph import Graphe
from .status import EtatCompetence, Statut


def _non_maitrise(etat: EtatCompetence) -> bool:
    return etat.statut in (Statut.ABSENT, Statut.FRAGILE)


def prerequis_transitifs_non_maitrises(
    cible: str,
    etats: Mapping[str, EtatCompetence],
    graphe: Graphe,
) -> set[str]:
    """Remonte les prérequis transitifs **non maîtrisés** d'une cible.

    On s'arrête aux nœuds maîtrisés (leur propre sous-graphe est présumé acquis) :
    c'est la frontière de ce qu'il reste à travailler pour atteindre ``cible``.
    """
    a_travailler: set[str] = set()
    pile = list(graphe.prerequis(cible))
    while pile:
        p = pile.pop()
        if p in a_travailler:
            continue
        etat = etats.get(p)
        if etat is None or _non_maitrise(etat):
            a_travailler.add(p)
            pile.extend(graphe.prerequis(p))
    return a_travailler


@dataclass
class Plan:
    """Plan de progression : nœuds ordonnés + échéances de révision."""

    noeuds_ordonnes: list[str]
    echeances: dict[str, dict[str, date]] = field(default_factory=dict)


def construire_plan(
    cible_noeuds: Iterable[str],
    etats: Mapping[str, EtatCompetence],
    graphe: Graphe,
    config: Config,
) -> Plan:
    """Construit le plan pour atteindre ``cible_noeuds``.

    - collecte les prérequis transitifs non maîtrisés de chaque cible, plus la
      cible elle-même si non maîtrisée ;
    - ordonne le tout topologiquement (prérequis avant dépendants) ;
    - programme J+2 / J+7 relativement à la date d'acquisition de chaque nœud
      déjà acquis (les nœuds non encore acquis auront leurs échéances à la volée).
    """
    a_travailler: set[str] = set()
    for cible in cible_noeuds:
        a_travailler |= prerequis_transitifs_non_maitrises(cible, etats, graphe)
        etat = etats.get(cible)
        if etat is None or _non_maitrise(etat):
            a_travailler.add(cible)

    # Ordre topologique restreint au périmètre à travailler.
    ordre = [nid for nid in graphe.ordre_topologique() if nid in a_travailler]

    echeances: dict[str, dict[str, date]] = {}
    for nid in ordre:
        etat = etats.get(nid)
        d_acq = etat.date_acquisition if etat else None
        if d_acq is not None:
            echeances[nid] = {
                "revision_j2": d_acq + timedelta(days=config.retention.revision_j2),
                "revision_j7": d_acq + timedelta(days=config.retention.revision_j7),
            }

    return Plan(noeuds_ordonnes=ordre, echeances=echeances)
