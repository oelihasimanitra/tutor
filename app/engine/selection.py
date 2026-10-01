"""Sélection du prochain item (test adaptatif).

Règles (SPEC §4-B / livrable 4) :
- nœud **maîtrisé** → on **monte** vers un successeur non maîtrisé ;
- nœud **non maîtrisé** avec des prérequis non maîtrisés → on **descend** vers un
  prérequis (les prérequis durs d'abord) ;
- sinon on pose un item du nœud courant.

La boucle est bornée par ``PROFONDEUR_MAX`` pour ne jamais boucler, même si le
graphe ou les états étaient incohérents. Le paramètre ``preferer_facile`` traduit
le pilotage par l'affect (anxiété élevée → items de difficulté minimale).
"""
from __future__ import annotations

import random
from typing import Mapping

from .graph import Graphe
from .items import Gabarit, ItemGenere, instancier
from .status import EtatCompetence, Statut

# Borne anti-boucle : nombre maximal de déplacements (montée/descente) autorisés.
PROFONDEUR_MAX = 50


def _non_maitrise(etat: EtatCompetence) -> bool:
    return etat.statut in (Statut.ABSENT, Statut.FRAGILE)


def prochain_item(
    graphe: Graphe,
    etats: Mapping[str, EtatCompetence],
    gabarits: Mapping[str, Gabarit],
    point_entree: str,
    rng: random.Random | None = None,
    preferer_facile: bool = False,
) -> ItemGenere | None:
    """Retourne le prochain item à poser, ou ``None`` si la branche est épuisée."""
    rng = rng or random.Random()
    noeud = point_entree

    for _ in range(PROFONDEUR_MAX):
        etat = etats.get(noeud) or EtatCompetence()

        # 1. Maîtrisé : monter vers un successeur non maîtrisé.
        if etat.statut in (Statut.ACQUIS, Statut.CONSOLIDE):
            suivants = [
                s for s in graphe.successeurs(noeud)
                if _non_maitrise(etats.get(s, EtatCompetence()))
            ]
            if not suivants:
                return None  # tout est maîtrisé sur cette branche
            noeud = suivants[0]
            continue

        # 2. Non maîtrisé : descendre vers un prérequis non maîtrisé s'il en existe.
        prerequis_non_maitrises = [
            p for p in graphe.prerequis(noeud)
            if _non_maitrise(etats.get(p, EtatCompetence()))
        ]
        if prerequis_non_maitrises:
            noeud = prerequis_non_maitrises[0]
            continue

        # 3. Prérequis maîtrisés (ou absents) : on attaque ce nœud.
        return _choisir_item(noeud, graphe, gabarits, rng, preferer_facile)

    return None


def _choisir_item(
    noeud: str,
    graphe: Graphe,
    gabarits: Mapping[str, Gabarit],
    rng: random.Random,
    preferer_facile: bool,
) -> ItemGenere | None:
    """Choisit un gabarit du nœud et l'instancie (seed aléatoire).

    ``preferer_facile`` restreint au gabarit de difficulté minimale (pilotage par
    l'affect). Un nœud sans gabarit est ignoré (cas limite, livrable 4).
    """
    ids_items = graphe[noeud].items
    candidats = [gabarits[i] for i in ids_items if i in gabarits]
    if not candidats:
        return None

    if preferer_facile:
        difficulte_min = min(g.difficulte for g in candidats)
        candidats = [g for g in candidats if g.difficulte == difficulte_min]

    gabarit = rng.choice(candidats)
    seed = rng.randrange(2**31)
    return instancier(gabarit, seed)
