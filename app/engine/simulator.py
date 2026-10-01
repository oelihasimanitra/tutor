"""Élèves simulés (SPEC §3.7) pour valider l'adaptatif avant les vrais élèves.

Chaque profil est une probabilité de réussite par compétence. On joue la boucle
adaptative contre l'élève simulé, puis on vérifie que les statuts convergent vers
le profil connu (l'adaptatif retrouve la compétence maîtrisée / la lacune).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Mapping

from .config import Config
from .graph import Graphe
from .items import Gabarit
from .selection import prochain_item
from .status import Reponse, calculer_etats


@dataclass
class EleveSimule:
    """Élève simulé : probabilité de réussite par compétence, défaut sinon."""

    par_defaut: float = 0.5
    competences: dict[str, float] = field(default_factory=dict)

    def reussit(self, competence_id: str, rng: random.Random) -> bool:
        p = self.competences.get(competence_id, self.par_defaut)
        return rng.random() < p


# Profils prédéfinis (cf. plan de tests, livrable 6).
PROFIL_MAITRISE = EleveSimule(par_defaut=0.9)
PROFIL_ALEATOIRE = EleveSimule(par_defaut=0.5)


def profil_lacune(noeud_lacune: str, p_ok: float = 0.9, p_lacune: float = 0.1) -> EleveSimule:
    """Profil qui maîtrise tout sauf une compétence (lacune ciblée)."""
    return EleveSimule(par_defaut=p_ok, competences={noeud_lacune: p_lacune})


def simuler_adaptatif(
    graphe: Graphe,
    gabarits: Mapping[str, Gabarit],
    eleve: EleveSimule,
    point_entree: str,
    config: Config,
    n_iterations: int,
    seed: int = 0,
) -> dict:
    """Joue ``n_iterations`` de la boucle adaptative contre un élève simulé.

    Retourne ``{"etats": ..., "reponses": {noeud: [Reponse, ...]}}``. Les dates
    des réponses croissent d'un jour par itération (utile pour J+7).
    """
    rng = random.Random(seed)
    reponses_par_noeud: dict[str, list[Reponse]] = {}
    etats: dict = {}
    jour = date(2026, 1, 1)

    for _ in range(n_iterations):
        etats = calculer_etats(graphe, reponses_par_noeud, config)
        item = prochain_item(graphe, etats, gabarits, point_entree, rng)
        if item is None:
            break
        correct = eleve.reussit(item.competence_id, rng)
        reponses_par_noeud.setdefault(item.competence_id, []).append(
            Reponse(competence_id=item.competence_id, est_correct=correct, date=jour)
        )
        jour += timedelta(days=1)

    etats = calculer_etats(graphe, reponses_par_noeud, config)
    return {"etats": etats, "reponses": reponses_par_noeud}
