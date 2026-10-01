"""Service de saisie tuteur : le pont entre le moteur (pur) et la persistance.

Phase 1 = outil tuteur. Le tuteur pose un item, l'élève travaille sur papier, le
tuteur saisit la réponse. Ce service orchestre :
- génération du prochain item (moteur) et **persistance** de l'item généré ;
- vérification de la réponse (moteur, sympy) ;
- enregistrement de la **réponse brute** (jamais modifiée ensuite) ;
- recalcul de la carte de compétences (moteur, état dérivé).

L'item généré est persisté (``items_generes``) et la réponse y est liée
(``item_id``) : le verdict reste ainsi **recalculable** depuis l'énoncé exact posé.
"""
from __future__ import annotations

from datetime import date
from typing import Mapping

from sqlmodel import Session, select

from ..engine.config import Config
from ..engine.graph import Graphe
from ..engine.items import Gabarit, ItemGenere as ItemMoteur, reponse_equivalente
from ..engine.selection import prochain_item as prochain_item_moteur
from ..engine.status import Reponse as ReponseMoteur, calculer_etats
from ..models import Eleve, ItemGenere as ItemGenereModel, Reponse


class TuteurService:
    """Orchestre la saisie tuteur pour un élève donné."""

    def __init__(self, session: Session, graphe: Graphe, gabarits: Mapping[str, Gabarit], config: Config):
        self.session = session
        self.graphe = graphe
        self.gabarits = gabarits
        self.config = config

    # --- Élève -----------------------------------------------------------
    def creer_eleve(self, pseudonyme: str) -> Eleve:
        """Crée un élève (pseudonyme uniquement — l'identité est une table séparée)."""
        eleve = Eleve(pseudonyme=pseudonyme)
        self.session.add(eleve)
        self.session.commit()
        self.session.refresh(eleve)
        return eleve

    # --- Saisie ----------------------------------------------------------
    def prochain_item(
        self,
        eleve_id: int,
        point_entree: str,
        preferer_facile: bool = False,
    ) -> ItemGenereModel | None:
        """Génère le prochain item (adaptatif), le persiste, et le retourne.

        Retourne ``None`` si la branche est épuisée (tout est maîtrisé).
        """
        etats = self._etats_moteur(eleve_id)
        item = prochain_item_moteur(
            self.graphe, etats, self.gabarits, point_entree,
            preferer_facile=preferer_facile,
        )
        if item is None:
            return None

        item_db = ItemGenereModel(
            gabarit_id=item.gabarit_id,
            variables=dict(item.variables),
            seed=item.seed,
            enonce=item.enonce,
            reponse_attendue=item.reponse_attendue,
        )
        self.session.add(item_db)
        self.session.commit()
        self.session.refresh(item_db)
        return item_db

    def enregistrer_reponse(
        self,
        eleve_id: int,
        item_db: ItemGenereModel,
        reponse_eleve: str,
        *,
        confiance_annoncee: int | None = None,
        type_erreur: str | None = None,
        methode_observee: str | None = None,
    ) -> Reponse:
        """Vérifie la réponse (sympy) et enregistre la réponse brute, liée à l'item."""
        est_correct = reponse_equivalente(item_db.reponse_attendue, reponse_eleve)
        competence_id = self.gabarits[item_db.gabarit_id].competence_id

        reponse = Reponse(
            eleve_id=eleve_id,
            item_id=item_db.id,
            competence_id=competence_id,
            reponse_eleve=reponse_eleve,
            est_correct=est_correct,
            confiance_annoncee=confiance_annoncee,
            type_erreur=type_erreur,
            methode_observee=methode_observee,
        )
        self.session.add(reponse)
        self.session.commit()
        self.session.refresh(reponse)
        return reponse

    # --- États dérivés ---------------------------------------------------
    def carte_competences(self, eleve_id: int) -> dict[str, "ReponseMoteur"]:
        """Recalcule la carte de compétences (état dérivé) depuis les réponses brutes."""
        return self._etats_moteur(eleve_id)

    def _etats_moteur(self, eleve_id: int) -> dict:
        """Convertit les réponses BDD en réponses moteur puis calcule les états."""
        reponses_db = self.session.exec(
            select(Reponse).where(Reponse.eleve_id == eleve_id)
        ).all()

        par_noeud: dict[str, list[ReponseMoteur]] = {}
        for r in reponses_db:
            if r.competence_id is None:
                continue
            par_noeud.setdefault(r.competence_id, []).append(ReponseMoteur(
                competence_id=r.competence_id,
                est_correct=bool(r.est_correct),
                date=(r.date.date() if r.date else date.today()),
                methode_observee=r.methode_observee,
                type_erreur=r.type_erreur,
                confiance_annoncee=r.confiance_annoncee,
            ))

        return calculer_etats(self.graphe, par_noeud, self.config)
