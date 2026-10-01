"""Import du contenu versionné (YAML) dans la base de données.

Le contenu vit sous Git (``app/content/``) et est importé en base (SPEC §3.5).
Ce module fait le pont : graphe → ``competences`` + ``prerequis``, gabarits →
``gabarits_items``. L'import est idempotent : ``merge`` par id pour les entités à
id stable, purge/réinsertion pour les prérequis (sans id métier).
"""
from __future__ import annotations

from typing import Mapping

from sqlmodel import Session, select

from ..engine.graph import Graphe
from ..engine.items import Gabarit
from ..models import Competence, GabaritItem, Prerequis


def importer_contenu(
    graphe: Graphe,
    gabarits: Mapping[str, Gabarit],
    session: Session,
) -> dict[str, int]:
    """Persiste compétences, prérequis et gabarits. Retourne les compteurs."""
    compteur = {"competences": 0, "prerequis": 0, "gabarits": 0}

    # Compétences : upsert par id (stable).
    for n in graphe.noeuds.values():
        session.merge(Competence(
            id=n.id,
            domaine=n.domaine,
            chapitre=n.chapitre,
            intitule=n.intitule,
            niveau_ref=n.niveau_ref,
            difficulte=n.difficulte,
            type=n.type,
            seuil_maitrise=dict(n.seuil_maitrise) if n.seuil_maitrise else None,
            erreurs_types=list(n.erreurs_types),
        ))
        compteur["competences"] += 1

    # Gabarits : upsert par id (stable).
    for g in gabarits.values():
        session.merge(GabaritItem(
            id=g.id,
            competence_id=g.competence_id,
            type=g.type,
            difficulte=g.difficulte,
            format_reponse=g.format_reponse,
            enonce=g.enonce,
            variables=dict(g.variables),
            reponse=g.reponse,
            methode=g.methode,
        ))
        compteur["gabarits"] += 1

    # Prérequis : purge puis réinsertion (pas d'id métier).
    for p in session.exec(select(Prerequis)).all():
        session.delete(p)
    for n in graphe.noeuds.values():
        for pre in n.prerequis:
            session.add(Prerequis(source_id=pre, cible_id=n.id, type_arete="dure"))
            compteur["prerequis"] += 1

    session.commit()
    return compteur
