"""Tests d'intégration des routes de saisie tuteur (phase 1).

On monte une application avec un lifespan **isolé** (base SQLite temporaire par
test, jamais ``tutorat.db``) pour éviter les conflits de verrou de fichier sous
Windows et rester hermétique entre tests — même pattern que ``tests/test_profil.py``.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.engine.config import load_config
from app.engine.content import charger_contenu
from app.models import create_db_and_tables, create_engine_sqlite
from app.services.importer import importer_contenu
from app.web.main import GRAPH_PATH, ITEMS_PATHS
from app.web.routes.tuteur import router

POINT_ENTREE = "NUM.ENT.01"


def _make_app(db_url: str) -> FastAPI:
    """Application de test : lifespan isolé sur une base temporaire + router tuteur."""

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        moteur = create_engine_sqlite(db_url)
        create_db_and_tables(moteur)
        config = load_config()
        graphe, gabarits = charger_contenu(GRAPH_PATH, ITEMS_PATHS)
        with Session(moteur) as session:
            importer_contenu(graphe, gabarits, session)
        app.state.engine = moteur
        app.state.config = config
        app.state.graphe = graphe
        app.state.gabarits = gabarits
        yield
        moteur.dispose()

    app = FastAPI(lifespan=_lifespan)
    app.include_router(router)
    return app


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    """Client de test sur une base SQLite jetable propre à chaque test."""
    db_url = f"sqlite:///{(tmp_path / 'test_routes.db').as_posix()}"
    with TestClient(_make_app(db_url)) as c:
        c.headers.update({"X-Tuteur-Pin": "tutor"})
        yield c


def test_parcours_complet(client: TestClient) -> None:
    """Créer élève -> prochain item -> saisir réponses -> carte de compétences."""
    # 1. Créer un élève.
    r = client.post("/eleves", json={"pseudonyme": "eleve-test-1"})
    assert r.status_code == 201
    eleve = r.json()
    assert eleve["pseudonyme"] == "eleve-test-1"
    assert isinstance(eleve["id"], int)
    eleve_id = eleve["id"]

    # 2. Prochain item — et surtout : PAS de reponse_attendue (sécurité élève).
    r = client.post(
        f"/eleves/{eleve_id}/items/prochain",
        json={"point_entree": POINT_ENTREE, "preferer_facile": True},
    )
    assert r.status_code == 200
    item = r.json()
    assert set(item) == {"item_id", "enonce", "competence_id", "gabarit_id"}
    assert "reponse_attendue" not in item
    assert item["competence_id"] == POINT_ENTREE
    assert item["enonce"]
    item_id = item["item_id"]

    # 3a. Réponse fausse -> verdict False, et là seulement la réponse attendue est exposée.
    r = client.post(
        f"/eleves/{eleve_id}/reponses",
        json={"item_id": item_id, "reponse_eleve": "999999999"},
    )
    assert r.status_code == 200
    fausse = r.json()
    assert fausse["est_correct"] is False
    assert isinstance(fausse["reponse_attendue"], str) and fausse["reponse_attendue"]
    assert isinstance(fausse["id"], int)

    # 3b. La réponse attendue (renvoyée après saisie) est acceptée comme correcte.
    r = client.post(
        f"/eleves/{eleve_id}/reponses",
        json={
            "item_id": item_id,
            "reponse_eleve": fausse["reponse_attendue"],
            "confiance_annoncee": 4,
            "type_erreur": None,
            "methode_observee": None,
        },
    )
    assert r.status_code == 200
    assert r.json()["est_correct"] is True

    # 4. Carte de compétences : 2 tentatives, 1 réussite sur le nœud visé.
    r = client.get(f"/eleves/{eleve_id}/competences")
    assert r.status_code == 200
    competences = r.json()["competences"]
    assert isinstance(competences, dict)
    etat = competences[POINT_ENTREE]
    assert set(etat) == {"statut", "origine", "nb_reussites", "nb_tentatives"}
    assert etat["nb_tentatives"] == 2
    assert etat["nb_reussites"] == 1
    assert etat["statut"] == "fragile"
    assert etat["origine"] == "mesure"


def test_prochain_item_reponse_toujours_absente(client: TestClient) -> None:
    """Garde-fou : « prochain item » n'expose jamais la réponse attendue."""
    eleve_id = client.post("/eleves", json={"pseudonyme": "eleve-test-2"}).json()["id"]
    r = client.post(
        f"/eleves/{eleve_id}/items/prochain",
        json={"point_entree": POINT_ENTREE},
    )
    assert r.status_code == 200
    assert "reponse_attendue" not in r.json()


def test_reponse_item_inconnu_404(client: TestClient) -> None:
    """Soumettre un item inexistant renvoie 404 (pas une erreur serveur)."""
    eleve_id = client.post("/eleves", json={"pseudonyme": "eleve-test-3"}).json()["id"]
    r = client.post(
        f"/eleves/{eleve_id}/reponses",
        json={"item_id": 999_999, "reponse_eleve": "1"},
    )
    assert r.status_code == 404


def test_pseudonyme_duplique_409(client: TestClient) -> None:
    """Un pseudonyme déjà pris renvoie 409 (contrainte d'unicité)."""
    assert client.post("/eleves", json={"pseudonyme": "dup"}).status_code == 201
    assert client.post("/eleves", json={"pseudonyme": "dup"}).status_code == 409


def test_routes_de_page_enregistrees(client: TestClient) -> None:
    """Les routes de page Jinja2 sont bien montées (rendu hors périmètre de ce test)."""
    chemins = set(client.get("/openapi.json").json()["paths"])
    assert "/" in chemins
    assert "/eleves/{eleve_id}" in chemins
    assert "/eleves/{eleve_id}/carte" in chemins
    # Les 4 endpoints API sont bien exposés eux aussi.
    assert "/eleves" in chemins
    assert "/eleves/{eleve_id}/items/prochain" in chemins
    assert "/eleves/{eleve_id}/reponses" in chemins
    assert "/eleves/{eleve_id}/competences" in chemins


def test_auth_requise_sans_pin(tmp_path):
    """Sans le PIN (header X-Tuteur-Pin), les routes de saisie renvoient 401."""
    db_url = f"sqlite:///{(tmp_path / 'test_auth.db').as_posix()}"
    with TestClient(_make_app(db_url)) as c:
        assert c.post("/eleves", json={"pseudonyme": "x"}).status_code == 401
        r = c.post("/eleves", json={"pseudonyme": "x"}, headers={"X-Tuteur-Pin": "tutor"})
        assert r.status_code == 201
