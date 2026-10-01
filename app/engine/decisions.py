"""Règles de décision du module D (protocole d'expérience de représentation).

SPEC §4-D : une condition (V/S/C/M) est **favorable** si elle dépasse les autres
d'**au moins 2 items sur 6** en ``T7_p`` **et** que l'ordre se retrouve au cycle 2.
- écart aux deux cycles → ``representation_efficace`` (hypothèse H renforcée) ;
- écart au cycle 1 seulement → H faible ;
- aucun écart → rester **multimodal** (``M``).

Hypothèses d'interprétation (configurables plus tard) :
- « dépasse les autres » = dépasse la *deuxième* meilleure condition ;
- si ``M`` est au moins aussi bonne que la meilleure condition simple, on reste
  multimodal (règle explicite du SPEC) ;
- deux gagnants contradictoires aux cycles 1 et 2 → prudence : multimodal.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

# Écart minimal en T7_p (sur 6 items) pour déclarer une condition gagnante.
ECART_MIN_ITEMS = 2


def decider_representation(blocs: Iterable[Mapping]) -> str:
    """Retourne la condition jugée efficace : ``'V'``, ``'S'``, ``'C'`` ou ``'M'``.

    ``blocs`` : itérable de dicts ``{condition, t7_p, cycle}`` (un bloc = une
    notion enseignée dans une condition, avec son score T7_p).
    """
    par_cycle: dict[int, list[Mapping]] = defaultdict(list)
    for b in blocs:
        par_cycle[b["cycle"]].append(b)

    gagnants: dict[int, str] = {}
    for cycle in sorted(par_cycle):
        bs = par_cycle[cycle]
        simples = [b for b in bs if b["condition"] != "M"]
        m = next((b for b in bs if b["condition"] == "M"), None)

        # Règle : M >= meilleure condition simple → rester multimodal.
        if simples and m is not None and m["t7_p"] >= max(b["t7_p"] for b in simples):
            continue

        # Une condition simple gagne si elle dépasse la 2e d'au moins 2 items.
        if len(simples) >= 2:
            simples_triees = sorted(simples, key=lambda b: -b["t7_p"])
            if simples_triees[0]["t7_p"] - simples_triees[1]["t7_p"] >= ECART_MIN_ITEMS:
                gagnants[cycle] = simples_triees[0]["condition"]

    if not gagnants:
        return "M"  # aucun écart → multimodal
    if len(gagnants) == 1:
        return list(gagnants.values())[0]  # H faible
    if len(set(gagnants.values())) == 1:
        return list(gagnants.values())[0]  # H renforcé (répliqué au cycle 2)
    return "M"  # gagnants contradictoires → prudence
