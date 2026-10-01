"""Graphe de compétences : chargement YAML, accès, validation d'acyclicité.

Le graphe est un **DAG** : une arête dure ``A -> B`` signifie « A est prérequis de
B ». Un cycle (A prérequis de B et B prérequis de A) serait une incohérence
pédagogique : on le rejette **au chargement** (SPEC §4-B / cas limites livrable 4).

On distingue deux sens de lecture :
- ``prerequis(noeud)`` : les nœuds qu'il faut maîtriser *avant* ``noeud`` ;
- ``successeurs(noeud)`` : les nœuds qui ont ``noeud`` comme prérequis (ce qu'on
  peut attaquer *après*).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml


@dataclass(frozen=True)
class Noeud:
    """Un nœud du graphe = une compétence (SPEC §4-B)."""

    id: str
    domaine: str
    chapitre: str
    intitule: str
    niveau_ref: str
    difficulte: int
    type: str  # procedure | concept | modelisation | raisonnement
    prerequis: tuple[str, ...] = ()        # arêtes DURES
    liens_faibles: tuple[str, ...] = ()    # arêtes faibles (non bloquantes)
    erreurs_types: tuple[str, ...] = ()
    items: tuple[str, ...] = ()            # ids des gabarits attachés
    seuil_maitrise: Mapping | None = None  # override optionnel du seuil global


class GrapheCycleError(ValueError):
    """Levée quand un cycle est détecté parmi les arêtes dures."""


@dataclass
class Graphe:
    """Conteneur des nœuds, indexé par id."""

    noeuds: dict[str, Noeud] = field(default_factory=dict)

    # -- accès pratiques -------------------------------------------------
    def __getitem__(self, node_id: str) -> Noeud:
        return self.noeuds[node_id]

    def __contains__(self, node_id: str) -> bool:
        return node_id in self.noeuds

    def __iter__(self):
        return iter(self.noeuds)

    def __len__(self) -> int:
        return len(self.noeuds)

    def ids(self) -> list[str]:
        return list(self.noeuds)

    # -- navigation ------------------------------------------------------
    def prerequis(self, node_id: str) -> list[str]:
        """Prérequis directs (arêtes dures) de ``node_id``."""
        return list(self.noeuds[node_id].prerequis)

    def successeurs(self, node_id: str) -> list[str]:
        """Les nœuds dont ``node_id`` est un prérequis direct."""
        return [n.id for n in self.noeuds.values() if node_id in n.prerequis]

    # -- validation ------------------------------------------------------
    def ordre_topologique(self) -> list[str]:
        """Tri topologique (algorithme de Kahn).

        Les prérequis sortent avant leurs dépendants. Lève :class:`GrapheCycleError`
        s'il reste des nœuds non triés (=> cycle). Gère les nœuds isolés.
        """
        indegree = {nid: len(n.prerequis) for nid, n in self.noeuds.items()}
        succ = {nid: self.successeurs(nid) for nid in self.noeuds}

        queue = deque(nid for nid, d in indegree.items() if d == 0)
        order: list[str] = []
        while queue:
            nid = queue.popleft()
            order.append(nid)
            for s in succ[nid]:
                indegree[s] -= 1
                if indegree[s] == 0:
                    queue.append(s)

        if len(order) != len(self.noeuds):
            restants = sorted(set(self.noeuds) - set(order))
            raise GrapheCycleError(
                f"cycle détecté dans les prérequis ; nœuds non triables : {restants}"
            )
        return order

    def valider(self) -> None:
        """Valide la cohérence interne : références de prérequis existantes + acyclicité.

        Lève :class:`KeyError` si un prérequis pointe vers un nœud inconnu, et
        :class:`GrapheCycleError` en cas de cycle.
        """
        for n in self.noeuds.values():
            for pre in n.prerequis:
                if pre not in self.noeuds:
                    raise KeyError(f"{n.id} référence un prérequis inconnu : {pre}")
        self.ordre_topologique()  # lève GrapheCycleError si cycle

    # -- chargement ------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str | Path) -> "Graphe":
        """Charge le graphe depuis un fichier YAML (format du livrable 5)."""
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        noeuds: dict[str, Noeud] = {}
        for d in raw["noeuds"]:
            n = Noeud(
                id=d["id"],
                domaine=d["domaine"],
                chapitre=d["chapitre"],
                intitule=d["intitule"],
                niveau_ref=d["niveau_ref"],
                difficulte=d["difficulte"],
                type=d["type"],
                prerequis=tuple(d.get("prerequis", [])),
                liens_faibles=tuple(d.get("liens_faibles", [])),
                erreurs_types=tuple(d.get("erreurs_types", [])),
                items=tuple(d.get("items", [])),
                seuil_maitrise=d.get("seuil_maitrise"),
            )
            noeuds[n.id] = n

        g = cls(noeuds=noeuds)
        g.valider()
        return g
