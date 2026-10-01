"""Statuts de compétence (état DÉRIVÉ) + propagation des prérequis.

Événements bruts → statut recalculable. Les réponses ne sont jamais modifiées :
on recompute l'état à la demande (SPEC §3.3). La propagation (un nœud maîtrisé
présume ses prérequis acquis) produit un statut inféré ``origine=propagation``,
qui sera confirmé par un item de contrôle — elle ne crée jamais de mesure.

Priorité des origines quand elles s'opposent : **mesure > controle > propagation**
(et ``M`` l'emporte toujours sur ``D``, SPEC §3.8).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Mapping

from .config import Config
from .graph import Graphe


class Statut(str, Enum):
    ABSENT = "absent"
    FRAGILE = "fragile"
    ACQUIS = "acquis"
    CONSOLIDE = "consolide"   # rétention validée à J+7


class Origine(str, Enum):
    MESURE = "mesure"
    PROPAGATION = "propagation"
    CONTROLE = "controle"


@dataclass(frozen=True)
class Reponse:
    """Une réponse brute (événement), version moteur — sans BDD.

    ``methode_observee`` sert au traçage de méthode (SPEC §4-B / point P2) :
    une réussite peut ne pas compter si la méthode n'est pas la bonne.
    """

    competence_id: str
    est_correct: bool
    date: datetime
    methode_observee: str | None = None
    type_erreur: str | None = None
    confiance_annoncee: int | None = None


@dataclass
class EtatCompetence:
    """État dérivé d'une compétence pour un élève donné."""

    statut: Statut = Statut.ABSENT
    origine: Origine = Origine.MESURE
    nb_reussites: int = 0
    nb_tentatives: int = 0
    date_acquisition: datetime | None = None
    date_consolidation: datetime | None = None


def statut_noeud(
    reponses: list[Reponse],
    config: Config,
    methode_attendue: str | None = None,
) -> EtatCompetence:
    """Calcule le statut « mesure » d'un nœud à partir de ses réponses brutes.

    - ``date_acquisition`` est **figée** au premier franchissement du seuil sur
      l'historique complet : elle ne dérive pas avec la fenêtre glissante.
    - le statut courant dépend de la fenêtre glissante des ``sur`` dernières
      tentatives (un échec récent peut faire retomber à ``fragile``).
    """
    seuil = config.seuil_maitrise
    reponses_triees = sorted(reponses, key=lambda r: r.date)

    def _ok(r: Reponse) -> bool:
        if not r.est_correct:
            return False
        if seuil.methode_correcte and methode_attendue and r.methode_observee != methode_attendue:
            return False
        return True

    # date_acquisition : premier franchissement du seuil sur l'historique complet.
    reussites_cumul = 0
    date_acq: datetime | None = None
    for r in reponses_triees:
        if _ok(r):
            reussites_cumul += 1
            if reussites_cumul >= seuil.reussites and date_acq is None:
                date_acq = r.date

    # Statut courant : fenêtre glissante des `sur` dernières tentatives.
    fenetre = reponses_triees[-seuil.sur:]
    reussites_fenetre = sum(1 for r in fenetre if _ok(r))
    etat = EtatCompetence(nb_tentatives=len(fenetre), nb_reussites=reussites_fenetre)

    # date_acquisition est figée au premier franchissement, indépendamment du
    # statut courant (un échec récent fait retomber à fragile, sans l'effacer).
    etat.date_acquisition = date_acq
    if reussites_fenetre >= seuil.reussites:
        etat.statut = Statut.ACQUIS
        etat.origine = Origine.MESURE
    elif fenetre:
        etat.statut = Statut.FRAGILE
    # sinon : ABSENT (défaut)

    return etat


def consolider(etat: EtatCompetence, reponses: list[Reponse], config: Config) -> EtatCompetence:
    """Passe ``acquis`` → ``consolide`` si une réussite existe à J+7 ou plus.

    La rétention se valide par un contrôle réussi au moins ``delai_jours`` jours
    après la date d'acquisition (SPEC §4-B : « rétention validée à J+7 »).
    """
    if etat.statut != Statut.ACQUIS or etat.date_acquisition is None:
        return etat
    seuil_date = etat.date_acquisition + timedelta(days=config.retention.delai_jours)
    for r in reponses:
        if r.est_correct and r.date >= seuil_date:
            etat.statut = Statut.CONSOLIDE
            etat.origine = Origine.CONTROLE
            etat.date_consolidation = r.date
            break
    return etat


def _propager_depuis(noeud_id: str, etats: dict[str, EtatCompetence], graphe: Graphe) -> None:
    """Marque les prérequis (transitifs) encore ``absent`` comme ``acquis`` par propagation."""
    pile = list(graphe.prerequis(noeud_id))
    while pile:
        pre = pile.pop()
        if etats[pre].statut == Statut.ABSENT:
            etats[pre].statut = Statut.ACQUIS
            etats[pre].origine = Origine.PROPAGATION
            pile.extend(graphe.prerequis(pre))


def calculer_etats(
    graphe: Graphe,
    reponses_par_noeud: Mapping[str, list[Reponse]],
    config: Config,
    methode_attendue_par_noeud: Mapping[str, str] | None = None,
) -> dict[str, EtatCompetence]:
    """Calcule tous les états (mesure + consolidation) puis propage les prérequis.

    - mesure : ``statut_noeud`` sur chaque nœud ;
    - consolidation : ``consolider`` si un contrôle J+7 existe ;
    - propagation : tout nœud maîtrisé (origine *mesure*) présume ses prérequis
      acquis, transitivement.
    """
    methode_attendue_par_noeud = methode_attendue_par_noeud or {}

    etats: dict[str, EtatCompetence] = {}
    for nid in graphe.ids():
        reponses = list(reponses_par_noeud.get(nid, []))
        e = statut_noeud(reponses, config, methode_attendue_par_noeud.get(nid))
        etats[nid] = consolider(e, reponses, config)

    for nid in graphe.ids():
        e = etats[nid]
        if e.statut in (Statut.ACQUIS, Statut.CONSOLIDE) and e.origine == Origine.MESURE:
            _propager_depuis(nid, etats, graphe)

    return etats
