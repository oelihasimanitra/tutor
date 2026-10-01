"""Chargement du contenu (graphe + gabarits) et validation croisée.

Le contenu est versionné sous Git puis importé en base (SPEC §3.5). Ici on le
charge en mémoire pour le moteur, en vérifiant la cohérence graphe ↔ gabarits :
- chaque item référencé par un nœud existe dans les gabarits ;
- chaque gabarit pointe vers une compétence existante.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .graph import Graphe
from .items import Gabarit, gabarits_from_yaml


def charger_contenu(
    graphe_path: str | Path,
    items_paths: Sequence[str | Path],
) -> tuple[Graphe, dict[str, Gabarit]]:
    """Charge graphe + gabarits et valide leur cohérence mutuelle."""
    graphe = Graphe.from_yaml(graphe_path)  # valide déjà l'acyclicité interne
    gabarits = gabarits_from_yaml(items_paths)

    for n in graphe.noeuds.values():
        for item_id in n.items:
            if item_id not in gabarits:
                raise KeyError(f"{n.id} référence un gabarit inconnu : {item_id}")

    for g in gabarits.values():
        if g.competence_id not in graphe:
            raise KeyError(
                f"le gabarit {g.id} référence une compétence inconnue : {g.competence_id}"
            )

    return graphe, gabarits
