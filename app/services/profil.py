"""Profil élève versionné + journal des changements + point d'entrée déduit.

Chaque appel à :meth:`ServiceProfil.creer_version_profil` crée une **nouvelle
version** (numéro « dernière + 1 ») et journalise les changements **champ par
champ** dans ``JournalProfil`` (ancienne/nouvelle valeur, statut D/M/H, raison).

Règle SPEC §3.8 « M l'emporte sur D » : un statut plus faible ne remplace jamais
un statut plus fort déjà acquis (priorité M > H > D). Comme la règle est
appliquée à chaque écriture, le statut porté par la version courante est toujours
le plus fort observé : comparer l'entrant à la version courante suffit.

Le point d'entrée dans le graphe est déduit du profil (SPEC §4-A) :
1. ``noeuds_suspects`` non vide -> le premier nœud suspect (priorité de vérification) ;
2. sinon ``niveau_declare`` correspondant à un ``niveau_ref`` du graphe -> le
   premier nœud de ce niveau dans l'ordre du graphe ;
3. sinon la racine du graphe (``NUM.ENT.01``).
"""
from __future__ import annotations

import json
from typing import Any

from sqlmodel import Session, select

from ..engine.graph import Graphe
from ..models import JournalProfil, Profil

# Normalisation des niveaux déclarés vers les `niveau_ref` du graphe.
ALIAS_NIVEAU = {
    "2nde": "seconde",
    "2de": "seconde",
}

# Racine du graphe : nœud sans prérequis, point d'entrée de repli.
RACINE = "NUM.ENT.01"

# Priorité des statuts (SPEC §3.8) : M > H > D.
PRIORITE_STATUT = {"M": 3, "H": 2, "D": 1}


def priorite_statut(statut: str | None) -> int:
    """Force relative d'un statut (M > H > D) ; inconnu = 0."""
    return PRIORITE_STATUT.get(statut or "", 0)


def _texte(valeur: Any) -> str | None:
    """Sérialise une valeur de champ en texte pour le journal (JSON si structuré)."""
    if valeur is None:
        return None
    if isinstance(valeur, str):
        return valeur
    return json.dumps(valeur, ensure_ascii=False, sort_keys=True)


def _premier_noeud(valeur: Any) -> str | None:
    """Premier élément exploitable d'une valeur ``noeuds_suspects`` (liste ou texte)."""
    if not valeur:
        return None
    if isinstance(valeur, str):
        morceaux = [m.strip() for m in valeur.replace(";", ",").split(",") if m.strip()]
        return morceaux[0] if morceaux else None
    if isinstance(valeur, (list, tuple)):
        for element in valeur:
            if element:
                return str(element)
        return None
    return str(valeur)


class ServiceProfil:
    """Orchestre le profil versionné d'un élève (persistance + déduction)."""

    def __init__(self, session: Session, graphe: Graphe):
        self.session = session
        self.graphe = graphe

    # --- Lecture ---------------------------------------------------------
    def profil_courant(self, eleve_id: int) -> Profil | None:
        """Dernière version du profil (``None`` si l'élève n'a pas encore de profil)."""
        return self.session.exec(
            select(Profil)
            .where(Profil.eleve_id == eleve_id)
            .order_by(Profil.version.desc())
        ).first()

    def journal(self, eleve_id: int) -> list[JournalProfil]:
        """Entrées de journal de l'élève, du plus récent au plus ancien."""
        return list(
            self.session.exec(
                select(JournalProfil)
                .where(JournalProfil.eleve_id == eleve_id)
                .order_by(JournalProfil.id.desc())
            ).all()
        )

    # --- Écriture --------------------------------------------------------
    def creer_version_profil(
        self,
        eleve_id: int,
        champs: dict,
        statuts: dict,
        raison: str | None = None,
    ) -> Profil:
        """Crée une nouvelle version du profil en fusionnant ``champs``/``statuts``.

        Les champs entrants sont fusionnés sur la version courante. Un champ
        entrant dont le statut est plus faible que le statut déjà acquis est
        **ignoré** (« M l'emporte sur D »). Chaque champ effectivement modifié est
        journalisé (ancienne valeur, nouvelle valeur, statut, raison).
        """
        courant = self.profil_courant(eleve_id)
        anciens_champs = dict(courant.champs) if courant else {}
        anciens_statuts = dict(courant.statuts) if courant else {}
        version = (courant.version + 1) if courant else 1

        nouveaux_champs = dict(anciens_champs)
        nouveaux_statuts = dict(anciens_statuts)
        changements: list[tuple[str, Any, Any, str]] = []

        for champ, nouvelle_valeur in champs.items():
            statut = statuts.get(champ) or "D"
            ancien_statut = anciens_statuts.get(champ)
            ancienne_valeur = anciens_champs.get(champ)

            # « M l'emporte sur D » : ne pas écraser un statut plus fort.
            if ancien_statut is not None and priorite_statut(statut) < priorite_statut(ancien_statut):
                continue
            # Rien à journaliser : valeur et statut inchangés.
            if champ in anciens_champs and ancienne_valeur == nouvelle_valeur and ancien_statut == statut:
                continue

            nouveaux_champs[champ] = nouvelle_valeur
            nouveaux_statuts[champ] = statut
            changements.append((champ, ancienne_valeur, nouvelle_valeur, statut))

        profil = Profil(
            eleve_id=eleve_id,
            version=version,
            raison=raison,
            champs=nouveaux_champs,
            statuts=nouveaux_statuts,
        )
        self.session.add(profil)
        self.session.flush()  # attribue l'id avant d'écrire le journal

        for champ, ancienne_valeur, nouvelle_valeur, statut in changements:
            self.session.add(
                JournalProfil(
                    eleve_id=eleve_id,
                    version=version,
                    champ=champ,
                    ancienne_valeur=_texte(ancienne_valeur),
                    nouvelle_valeur=_texte(nouvelle_valeur),
                    statut=statut,
                    raison=raison,
                )
            )

        self.session.commit()
        self.session.refresh(profil)
        return profil

    # --- Point d'entrée --------------------------------------------------
    def deduire_point_entree(self, profil: Profil | None, graphe: Graphe) -> str:
        """Déduit le nœud d'entrée du test adaptatif depuis le profil."""
        champs = profil.champs if profil else {}

        premier_suspect = _premier_noeud(champs.get("noeuds_suspects"))
        if premier_suspect:
            return premier_suspect

        niveau = champs.get("niveau_declare")
        if isinstance(niveau, str) and niveau.strip():
            cible = ALIAS_NIVEAU.get(niveau.strip(), niveau.strip())
            for noeud_id in graphe.ids():  # ordre du graphe (ordre du YAML)
                if graphe[noeud_id].niveau_ref == cible:
                    return noeud_id

        return RACINE
