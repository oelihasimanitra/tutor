"""Routes du profil élève versionné : entretien, profil, journal, point d'entrée.

Même pattern que ``routes/tuteur.py`` : le service est construit **par requête**
(via une dépendance ``get_service`` qui ferme la session en fin de requête) sur
l'état exposé par le lifespan dans ``app.state`` (``engine``, ``graphe``).

COLLISION DE CHEMINS — ``GET /eleves/{eleve_id}/profil`` est demandé à la fois
comme API JSON (version courante) et comme page Jinja2 (profil + journal). Deux
routes ne peuvent pas partager chemin et méthode : on résout la collision par
**négociation de contenu** sur ce même chemin — un client qui demande du HTML
(``Accept: text/html``, cas d'une navigation navigateur) reçoit la page, les
autres (API, HTMX/fetch, ``*/*``) reçoivent le JSON. Le chemin de page explicite
``/eleves/{eleve_id}/profil-page`` est aussi exposé comme alias sans ambiguïté.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.models import Eleve
from app.services.codage import coder_reponses, structure_entretien
from app.services.profil import ServiceProfil

from ..schemas_profil import (
    EntretienRequete,
    JournalEntreeOut,
    JournalOut,
    PointEntreeOut,
    ProfilOut,
)

router = APIRouter()

# Templates servis par les routes de page (mêmes conventions que routes/tuteur.py).
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_service(request: Request) -> Iterator[ServiceProfil]:
    """Construit un ``ServiceProfil`` sur une session fraîche, fermée après usage."""
    with Session(request.app.state.engine) as session:
        yield ServiceProfil(session, request.app.state.graphe)


def _eleve_ou_404(service: ServiceProfil, eleve_id: int) -> Eleve:
    eleve = service.session.get(Eleve, eleve_id)
    if eleve is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Élève introuvable.")
    return eleve


def _profil_out(profil) -> ProfilOut:
    return ProfilOut(version=profil.version, champs=profil.champs, statuts=profil.statuts)


def _veut_html(request: Request) -> bool:
    """Vrai si le client demande explicitement du HTML (navigation navigateur)."""
    return "text/html" in request.headers.get("accept", "")


def _contexte_page_profil(service: ServiceProfil, eleve_id: int):
    """Contexte du template ``profil.html`` (profil courant + journal + point d'entrée)."""
    eleve = _eleve_ou_404(service, eleve_id)
    profil = service.profil_courant(eleve_id)
    journal = service.journal(eleve_id)
    point_entree = service.deduire_point_entree(profil, service.graphe) if profil else None
    return {
        "eleve_id": eleve_id,
        "eleve": eleve,
        "profil": profil,
        "journal": journal,
        "point_entree": point_entree,
        "titre": f"Profil — {eleve.pseudonyme}",
    }


# --- API JSON ----------------------------------------------------------------

@router.post(
    "/eleves/{eleve_id}/entretien",
    response_model=ProfilOut,
    status_code=status.HTTP_201_CREATED,
)
def saisir_entretien(
    eleve_id: int,
    payload: EntretienRequete,
    service: ServiceProfil = Depends(get_service),
) -> ProfilOut:
    """Code les réponses de l'entretien et crée une nouvelle version du profil."""
    _eleve_ou_404(service, eleve_id)
    champs, statuts = coder_reponses(payload.reponses)
    profil = service.creer_version_profil(eleve_id, champs, statuts, payload.raison)
    return _profil_out(profil)


@router.get("/eleves/{eleve_id}/profil", response_model=ProfilOut)
def lire_profil(
    request: Request,
    eleve_id: int,
    service: ServiceProfil = Depends(get_service),
) -> ProfilOut | HTMLResponse:
    """Version courante du profil, ou page HTML si le client demande du HTML.

    - ``Accept: text/html`` (navigateur) -> ``profil.html`` (profil + journal).
    - sinon -> JSON ``ProfilOut`` (404 si l'élève n'a pas encore de profil).
    """
    if _veut_html(request):
        return templates.TemplateResponse(
            request, "profil.html", _contexte_page_profil(service, eleve_id)
        )
    profil = service.profil_courant(eleve_id)
    if profil is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun profil pour cet élève.")
    return _profil_out(profil)


@router.get("/eleves/{eleve_id}/journal", response_model=JournalOut)
def lire_journal(
    eleve_id: int,
    service: ServiceProfil = Depends(get_service),
) -> JournalOut:
    """Journal des changements de profil, du plus récent au plus ancien."""
    return JournalOut(
        journal=[
            JournalEntreeOut(
                champ=entree.champ,
                ancienne_valeur=entree.ancienne_valeur,
                nouvelle_valeur=entree.nouvelle_valeur,
                statut=entree.statut,
                raison=entree.raison,
                date=entree.date,
            )
            for entree in service.journal(eleve_id)
        ]
    )


@router.get("/eleves/{eleve_id}/point-entree", response_model=PointEntreeOut)
def lire_point_entree(
    eleve_id: int,
    service: ServiceProfil = Depends(get_service),
) -> PointEntreeOut:
    """Point d'entrée déduit du profil courant (404 si aucun profil)."""
    profil = service.profil_courant(eleve_id)
    if profil is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun profil pour cet élève.")
    return PointEntreeOut(point_entree=service.deduire_point_entree(profil, service.graphe))


# --- Pages Jinja2 ------------------------------------------------------------

@router.get("/eleves/{eleve_id}/entretien", response_class=HTMLResponse)
def page_entretien(
    request: Request,
    eleve_id: int,
    service: ServiceProfil = Depends(get_service),
) -> HTMLResponse:
    """Page de saisie de l'entretien (structure chargée depuis ``entretien.yaml``)."""
    eleve = _eleve_ou_404(service, eleve_id)
    return templates.TemplateResponse(
        request,
        "entretien.html",
        {
            "eleve_id": eleve_id,
            "eleve": eleve,
            "blocs": structure_entretien(),
            "titre": f"Entretien — {eleve.pseudonyme}",
        },
    )


@router.get("/eleves/{eleve_id}/profil-page", response_class=HTMLResponse)
def page_profil(
    request: Request,
    eleve_id: int,
    service: ServiceProfil = Depends(get_service),
) -> HTMLResponse:
    """Page du profil vivant (alias HTML explicite de ``GET /profil``)."""
    return templates.TemplateResponse(
        request, "profil.html", _contexte_page_profil(service, eleve_id)
    )
