"""Routes de saisie tuteur (phase 1) : 4 endpoints API + pages Jinja2.

Le service ``TuteurService`` est construit **par requête** (une session SQLModel
n'est pas partagée entre requêtes) via une dépendance ``yield`` qui garantit la
fermeture de la session en fin de requête.

Règle de sécurité : l'endpoint « prochain item » ne renvoie jamais la réponse
attendue — elle n'est exposée qu'après la saisie (``ReponseOut``).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.models import Eleve, ItemGenere
from app.services.tuteur import TuteurService

from ..auth import verifier_pin

from ..schemas import (
    CarteCompetencesOut,
    CompetenceOut,
    EleveCreation,
    EleveOut,
    ProchainItemOut,
    ProchainItemRequete,
    ReponseOut,
    ReponseSaisie,
)

router = APIRouter(dependencies=[Depends(verifier_pin)])

# Templates servis par les routes de page (produits en parallèle côté front).
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_service(request: Request) -> Iterator[TuteurService]:
    """Construit un ``TuteurService`` sur une session fraîche, fermée après usage.

    L'état applicatif (engine, graphe, gabarits, config) est exposé par le
    lifespan dans ``app.state`` (cf. ``app/web/main.py``).
    """
    with Session(request.app.state.engine) as session:
        yield TuteurService(
            session,
            request.app.state.graphe,
            request.app.state.gabarits,
            request.app.state.config,
        )


# --- API JSON ----------------------------------------------------------------

@router.post("/eleves", response_model=EleveOut, status_code=status.HTTP_201_CREATED)
def creer_eleve(payload: EleveCreation, service: TuteurService = Depends(get_service)) -> EleveOut:
    """Crée un élève (pseudonyme unique)."""
    try:
        eleve = service.creer_eleve(payload.pseudonyme)
    except IntegrityError:
        # Pseudonyme déjà pris (contrainte UNIQUE) : conflit, pas une erreur serveur.
        service.session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Pseudonyme déjà utilisé.")
    return EleveOut(id=eleve.id, pseudonyme=eleve.pseudonyme)


@router.post(
    "/eleves/{eleve_id}/items/prochain",
    response_model=ProchainItemOut,
    responses={204: {"description": "Branche épuisée : plus rien à poser."}},
)
def prochain_item(
    eleve_id: int,
    payload: ProchainItemRequete,
    service: TuteurService = Depends(get_service),
) -> ProchainItemOut | Response:
    """Génère et persiste le prochain item adaptatif (sans la réponse attendue)."""
    item = service.prochain_item(
        eleve_id,
        payload.point_entree,
        preferer_facile=payload.preferer_facile,
    )
    if item is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    competence_id = service.gabarits[item.gabarit_id].competence_id
    return ProchainItemOut(
        item_id=item.id,
        enonce=item.enonce,
        competence_id=competence_id,
        gabarit_id=item.gabarit_id,
    )


@router.post("/eleves/{eleve_id}/reponses", response_model=ReponseOut)
def enregistrer_reponse(
    eleve_id: int,
    payload: ReponseSaisie,
    service: TuteurService = Depends(get_service),
) -> ReponseOut:
    """Vérifie et enregistre la réponse brute, puis renvoie le feedback tuteur."""
    item = service.session.get(ItemGenere, payload.item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item introuvable.")

    reponse = service.enregistrer_reponse(
        eleve_id,
        item,
        payload.reponse_eleve,
        confiance_annoncee=payload.confiance_annoncee,
        type_erreur=payload.type_erreur,
        methode_observee=payload.methode_observee,
    )
    return ReponseOut(
        id=reponse.id,
        est_correct=bool(reponse.est_correct),
        reponse_attendue=item.reponse_attendue,
    )


@router.get("/eleves/{eleve_id}/competences", response_model=CarteCompetencesOut)
def carte_competences(
    eleve_id: int,
    service: TuteurService = Depends(get_service),
) -> CarteCompetencesOut:
    """Carte de compétences recalculée (état dérivé), enums sérialisés."""
    carte = service.carte_competences(eleve_id)
    return CarteCompetencesOut(
        competences={
            noeud_id: CompetenceOut(
                statut=etat.statut.value,
                origine=etat.origine.value,
                nb_reussites=etat.nb_reussites,
                nb_tentatives=etat.nb_tentatives,
            )
            for noeud_id, etat in carte.items()
        }
    )


# --- Pages Jinja2 ------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def page_index(request: Request) -> HTMLResponse:
    """Page d'accueil (sélection / création d'élève)."""
    return templates.TemplateResponse(request, "index.html", {"titre": "Suivi de tutorat"})


@router.get("/eleves/{eleve_id}", response_class=HTMLResponse)
def page_eleve(request: Request, eleve_id: int, service: TuteurService = Depends(get_service)) -> HTMLResponse:
    """Espace de saisie d'un élève."""
    eleve = service.session.get(Eleve, eleve_id)
    return templates.TemplateResponse(
        request, "eleve.html", {"eleve_id": eleve_id, "eleve": eleve, "titre": f"Élève {eleve_id}"}
    )


@router.get("/eleves/{eleve_id}/carte", response_class=HTMLResponse)
def page_carte(request: Request, eleve_id: int, service: TuteurService = Depends(get_service)) -> HTMLResponse:
    """Page de la carte de compétences (distincte de l'API JSON homonyme).

    Passe les compétences sérialisées au template pour que le tableau soit
    rempli dès le premier rendu (sans dépendre du JS/HTMX).
    """
    eleve = service.session.get(Eleve, eleve_id)
    carte = service.carte_competences(eleve_id)
    competences = {
        noeud_id: {
            "statut": etat.statut.value,
            "origine": etat.origine.value,
            "nb_reussites": etat.nb_reussites,
            "nb_tentatives": etat.nb_tentatives,
        }
        for noeud_id, etat in carte.items()
    }
    return templates.TemplateResponse(
        request,
        "competences.html",
        {
            "eleve_id": eleve_id,
            "eleve": eleve,
            "competences": competences,
            "titre": f"Carte — élève {eleve_id}",
        },
    )
