"""Tests du profil élève versionné (service) et de ses routes (API + pages).

- Service : versionnage, journalisation champ par champ, règle « M l'emporte sur
  D », et déduction du point d'entrée.
- Codage : transformation des réponses de l'entretien en ``(champs, statuts)``.
- Routes : parcours complet via ``TestClient`` (entretien -> profil -> journal ->
  point d'entrée, plus le rendu des pages Jinja2).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

import app.models  # noqa: F401  (enregistre les tables dans SQLModel.metadata)
from app.engine.config import load_config
from app.engine.content import charger_contenu
from app.models import Eleve, create_db_and_tables, create_engine_sqlite
from app.services.codage import coder_reponses
from app.services.importer import importer_contenu
from app.services.profil import ServiceProfil
from app.web.main import GRAPH_PATH, ITEMS_PATHS
from app.web.routes.profil import router as profil_router
from app.web.routes.tuteur import router as tuteur_router


# --- Fixtures ---------------------------------------------------------------

@pytest.fixture()
def session() -> Iterator[Session]:
    """Base SQLite en mémoire partagée (StaticPool) pour les tests de service."""
    moteur = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(moteur)
    with Session(moteur) as s:
        yield s
    moteur.dispose()


@pytest.fixture()
def service(session, graphe) -> ServiceProfil:
    return ServiceProfil(session, graphe)


def _creer_eleve(service: ServiceProfil, pseudonyme: str = "eleve-profil") -> Eleve:
    eleve = Eleve(pseudonyme=pseudonyme)
    service.session.add(eleve)
    service.session.commit()
    service.session.refresh(eleve)
    return eleve


# --- Codage des réponses de l'entretien -------------------------------------

def test_codage_anxiete_et_mindset_par_somme():
    """anxiete = somme des 6 items ; mindset = somme des 4 items (statut D)."""
    reponses = {
        "bloc3.anxiete.q1": 5,
        "bloc3.anxiete.q2": 5,
        "bloc3.anxiete.q3": 4,
        "bloc3.anxiete.q4": 3,
        "bloc3.anxiete.q5": 2,
        "bloc3.anxiete.q6": 1,
        "bloc3.mindset.q1": 3,
        "bloc3.mindset.q2": 3,
        "bloc3.mindset.q3": 3,
        "bloc3.mindset.q4": 3,
    }
    champs, statuts = coder_reponses(reponses)
    assert champs["anxiete"] == 20
    assert champs["mindset"] == 12
    assert statuts["anxiete"] == "D"
    assert statuts["mindset"] == "D"


def test_codage_niveau_declare_normalise():
    """niveau_declare est normalisé en niveau scolaire, pas laissé en code A-F."""
    champs, _ = coder_reponses({"bloc1.niveau_declare.q1": "A: 5e"})
    assert champs["niveau_declare"] == "5e"

    champs, _ = coder_reponses({"bloc1.niveau_declare.q1": "D: 2nde"})
    assert champs["niveau_declare"] == "seconde"  # vocabulaire du graphe


def test_codage_choix_mappe_par_le_codage_yaml():
    """Quand le codage déclare « A -> jeton », le jeton est retenu."""
    champs, statuts = coder_reponses({"bloc1.tendance.q1": "A"})
    assert champs["tendance"] == "en_baisse"
    assert statuts["tendance"] == "D"


def test_codage_noeuds_suspects_en_liste_statut_h():
    """noeuds_suspects devient une liste, avec le statut hypothèse (H)."""
    champs, statuts = coder_reponses(
        {"bloc1.noeuds_suspects.q1": "NUM.FRA.01, ALG.EQ1.01"}
    )
    assert champs["noeuds_suspects"] == ["NUM.FRA.01", "ALG.EQ1.01"]
    assert statuts["noeuds_suspects"] == "H"


def test_codage_autoeval_en_dictionnaire():
    """autoeval[domaine] produit un dict {domaine: entier} sous le champ autoeval."""
    champs, _ = coder_reponses(
        {"bloc3.autoeval.q1": {"NUM": 3, "ALG": "4", "LOG": 5}}
    )
    assert champs["autoeval"] == {"NUM": 3, "ALG": 4, "LOG": 5}


def test_codage_ignore_les_questions_inconnues():
    """Un identifiant de question inconnu est ignoré (pas d'exception)."""
    champs, statuts = coder_reponses({"question.bidon.q1": 42})
    assert champs == {}
    assert statuts == {}


# --- Service : versionnage et journalisation --------------------------------

def test_premiere_version_et_journal(service):
    """La première version est la version 1 ; chaque champ neuf est journalisé."""
    eleve = _creer_eleve(service)
    profil = service.creer_version_profil(
        eleve.id,
        {"niveau_declare": "5e", "tendance": "stable"},
        {"niveau_declare": "D", "tendance": "D"},
        raison="entretien de départ",
    )
    assert profil.version == 1
    assert profil.champs == {"niveau_declare": "5e", "tendance": "stable"}
    assert profil.raison == "entretien de départ"

    entrees = service.journal(eleve.id)
    assert len(entrees) == 2
    par_champ = {e.champ: e for e in entrees}
    assert par_champ["niveau_declare"].ancienne_valeur is None
    assert par_champ["niveau_declare"].nouvelle_valeur == "5e"
    assert par_champ["niveau_declare"].statut == "D"
    assert par_champ["niveau_declare"].raison == "entretien de départ"


def test_versionnage_incremente_et_fusionne(service):
    """Chaque appel crée la version suivante, en fusionnant les champs."""
    eleve = _creer_eleve(service, "eleve-version")
    service.creer_version_profil(eleve.id, {"a": "1"}, {"a": "D"})
    v2 = service.creer_version_profil(
        eleve.id, {"b": "2"}, {"b": "D"}, raison="complément"
    )
    assert v2.version == 2
    assert v2.champs == {"a": "1", "b": "2"}  # fusion, pas remplacement
    assert v2.statuts == {"a": "D", "b": "D"}


def test_journalisation_ancienne_et_nouvelle_valeur(service):
    """Un changement de valeur est journalisé avec ancienne et nouvelle valeur."""
    eleve = _creer_eleve(service, "eleve-journal")
    service.creer_version_profil(eleve.id, {"objectif": "rattraper"}, {"objectif": "D"})
    service.creer_version_profil(eleve.id, {"objectif": "examen"}, {"objectif": "D"})

    entrees = service.journal(eleve.id)
    # Plus récent d'abord : le changement de la version 2 arrive en tête.
    assert entrees[0].version == 2
    assert entrees[0].champ == "objectif"
    assert entrees[0].ancienne_valeur == "rattraper"
    assert entrees[0].nouvelle_valeur == "examen"
    assert entrees[-1].version == 1


def test_journal_du_plus_recent_au_plus_ancien(service):
    """Le journal est trié du plus récent au plus ancien."""
    eleve = _creer_eleve(service, "eleve-tri")
    service.creer_version_profil(eleve.id, {"x": "1"}, {"x": "D"})
    service.creer_version_profil(eleve.id, {"x": "2"}, {"x": "D"})
    entrees = service.journal(eleve.id)
    assert [e.nouvelle_valeur for e in entrees] == ["2", "1"]


def test_m_lemporte_sur_d(service):
    """Un statut plus faible n'écrase pas un statut plus fort déjà acquis."""
    eleve = _creer_eleve(service, "eleve-md")
    # 1. Une valeur MESURÉE (M) est posée.
    v1 = service.creer_version_profil(
        eleve.id, {"calibration": 1}, {"calibration": "M"}, raison="mesure"
    )
    assert v1.statuts["calibration"] == "M"

    # 2. Une valeur DÉCLARÉE (D) tente de la remplacer : M l'emporte.
    v2 = service.creer_version_profil(
        eleve.id, {"calibration": 99}, {"calibration": "D"}, raison="déclaré"
    )
    assert v2.version == 2
    assert v2.champs["calibration"] == 1
    assert v2.statuts["calibration"] == "M"
    # Aucun changement n'a été journalisé pour ce champ dans la version 2.
    assert all(e.champ != "calibration" for e in service.journal(eleve.id) if e.version == 2)

    # 3. Une nouvelle mesure (M) plus forte remplace bien la précédente.
    v3 = service.creer_version_profil(
        eleve.id, {"calibration": 2}, {"calibration": "M"}, raison="nouvelle mesure"
    )
    assert v3.champs["calibration"] == 2
    assert any(e.champ == "calibration" and e.version == 3 for e in service.journal(eleve.id))


def test_d_statut_faible_mais_valeur_mesure_reste(service):
    """H (hypothèse) est plus fort que D : H est conservé face à un D ultérieur."""
    eleve = _creer_eleve(service, "eleve-h")
    service.creer_version_profil(eleve.id, {"p": "init"}, {"p": "H"})
    v = service.creer_version_profil(eleve.id, {"p": "autre"}, {"p": "D"})
    assert v.champs["p"] == "init"
    assert v.statuts["p"] == "H"


# --- Service : point d'entrée déduit ----------------------------------------

def test_point_entree_noeuds_suspects_prioritaires(service):
    """noeuds_suspects non vide -> le premier nœud suspect."""
    eleve = _creer_eleve(service, "eleve-entree-suspects")
    profil = service.creer_version_profil(
        eleve.id,
        {"niveau_declare": "5e", "noeuds_suspects": ["ALG.EQ1.01", "NUM.FRA.01"]},
        {"niveau_declare": "D", "noeuds_suspects": "H"},
    )
    assert service.deduire_point_entree(profil, service.graphe) == "ALG.EQ1.01"


def test_point_entree_par_niveau_declare(service):
    """Sans suspect, le point d'entrée est le premier nœud du niveau déclaré."""
    eleve = _creer_eleve(service, "eleve-entree-niveau")
    profil = service.creer_version_profil(
        eleve.id, {"niveau_declare": "5e"}, {"niveau_declare": "D"}
    )
    attendu = next(nid for nid in service.graphe.ids() if service.graphe[nid].niveau_ref == "5e")
    assert service.deduire_point_entree(profil, service.graphe) == attendu
    assert attendu == "NUM.ENT.01"  # premier nœud du graphe


def test_point_entree_repli_racine(service):
    """Profil sans niveau exploitable -> racine du graphe (NUM.ENT.01)."""
    eleve = _creer_eleve(service, "eleve-entree-racine")
    profil = service.creer_version_profil(
        eleve.id, {"objectif": "examen"}, {"objectif": "D"}
    )
    assert service.deduire_point_entree(profil, service.graphe) == "NUM.ENT.01"


def test_point_entree_profil_none(service):
    """Profil absent -> racine du graphe."""
    assert service.deduire_point_entree(None, service.graphe) == "NUM.ENT.01"


# --- Routes (TestClient) ----------------------------------------------------

def _make_app(db_url: str) -> FastAPI:
    """Application de test montée sur une base **temporaire** (jamais tutorat.db)."""

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
    app.include_router(tuteur_router)
    app.include_router(profil_router)
    return app


@pytest.fixture()
def client(tmp_path) -> Iterator[TestClient]:
    """Client de test sur une base SQLite jetable propre à chaque test."""
    db_url = f"sqlite:///{(tmp_path / 'test_profil.db').as_posix()}"
    with TestClient(_make_app(db_url)) as c:
        yield c


def _nouvel_eleve(client: TestClient, pseudonyme: str) -> int:
    return client.post("/eleves", json={"pseudonyme": pseudonyme}).json()["id"]


def test_route_entretien_cree_profil(client: TestClient):
    """POST entretien -> 201 avec version, champs codés et statuts."""
    eleve_id = _nouvel_eleve(client, "route-entretien")
    reponses = {
        "bloc1.niveau_declare.q1": "A: 5e",
        "bloc3.anxiete.q1": 4,
        "bloc3.anxiete.q2": 4,
        "bloc3.anxiete.q3": 4,
        "bloc3.anxiete.q4": 4,
        "bloc3.anxiete.q5": 4,
        "bloc3.anxiete.q6": 4,
    }
    r = client.post(
        f"/eleves/{eleve_id}/entretien",
        json={"reponses": reponses, "raison": "entretien de départ"},
    )
    assert r.status_code == 201
    corps = r.json()
    assert corps["version"] == 1
    assert corps["champs"]["anxiete"] == 24
    assert corps["champs"]["niveau_declare"] == "5e"
    assert corps["statuts"]["anxiete"] == "D"


def test_route_profil_et_404(client: TestClient):
    """GET profil : 404 tant qu'aucun entretien, puis 200 avec la bonne version."""
    eleve_id = _nouvel_eleve(client, "route-profil")
    assert client.get(f"/eleves/{eleve_id}/profil").status_code == 404

    client.post(
        f"/eleves/{eleve_id}/entretien",
        json={"reponses": {"bloc1.objectif.q1": "D"}},
    )
    r = client.get(f"/eleves/{eleve_id}/profil")
    assert r.status_code == 200
    assert r.json()["version"] == 1
    assert "objectif" in r.json()["champs"]


def test_route_journal(client: TestClient):
    """GET journal renvoie les entrées du plus récent au plus ancien."""
    eleve_id = _nouvel_eleve(client, "route-journal")
    client.post(
        f"/eleves/{eleve_id}/entretien",
        json={"reponses": {"bloc1.objectif.q1": "A"}, "raison": "v1"},
    )
    client.post(
        f"/eleves/{eleve_id}/entretien",
        json={"reponses": {"bloc1.objectif.q1": "B"}, "raison": "v2"},
    )
    r = client.get(f"/eleves/{eleve_id}/journal")
    assert r.status_code == 200
    journal = r.json()["journal"]
    assert len(journal) == 2
    # Le plus récent (v2) est en tête, et les champs du contrat sont présents.
    assert journal[0]["champ"] == "objectif"
    assert set(journal[0]) == {
        "champ", "ancienne_valeur", "nouvelle_valeur", "statut", "raison", "date",
    }
    # Le code A/B est conservé (pas de mapping « -> » dans le codage d'objectif).
    assert journal[0]["ancienne_valeur"] == "A"
    assert journal[0]["nouvelle_valeur"] == "B"
    assert journal[0]["statut"] == "D"
    assert journal[0]["raison"] == "v2"
    assert journal[0]["date"]


def test_route_point_entree_et_404(client: TestClient):
    """GET point-entree : 404 sans profil, puis déduit depuis noeuds_suspects."""
    eleve_id = _nouvel_eleve(client, "route-entree")
    assert client.get(f"/eleves/{eleve_id}/point-entree").status_code == 404

    client.post(
        f"/eleves/{eleve_id}/entretien",
        json={"reponses": {"bloc1.noeuds_suspects.q1": "ALG.EQ1.01, NUM.FRA.01"}},
    )
    r = client.get(f"/eleves/{eleve_id}/point-entree")
    assert r.status_code == 200
    assert r.json() == {"point_entree": "ALG.EQ1.01"}


def test_route_entretien_eleve_inconnu_404(client: TestClient):
    """POST entretien pour un élève inexistant -> 404 (pas d'erreur serveur)."""
    r = client.post("/eleves/999999/entretien", json={"reponses": {}})
    assert r.status_code == 404


def test_pages_entretien_et_profil(client: TestClient):
    """Les pages Jinja2 se rendent (entretien : structure ; profil : vivant + journal)."""
    eleve_id = _nouvel_eleve(client, "route-pages")

    r = client.get(f"/eleves/{eleve_id}/entretien")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Entretien de départ" in r.text

    client.post(
        f"/eleves/{eleve_id}/entretien",
        json={"reponses": {"bloc1.niveau_declare.q1": "A: 5e"}, "raison": "initial"},
    )
    # Alias HTML explicite.
    r = client.get(f"/eleves/{eleve_id}/profil-page")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Profil vivant" in r.text
    assert "niveau_declare" in r.text

    # Même chemin que l'API JSON, mais page quand le client demande du HTML.
    r = client.get(f"/eleves/{eleve_id}/profil", headers={"accept": "text/html"})
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Profil vivant" in r.text

    # Sans préférence HTML (API/HTMX), GET /profil renvoie le JSON.
    r = client.get(f"/eleves/{eleve_id}/profil")
    assert r.status_code == 200
    assert r.json()["version"] == 1


def test_routes_enregistrees(client: TestClient):
    """Les routes API et de page sont bien montées dans l'application."""
    chemins = set(client.get("/openapi.json").json()["paths"])
    assert "/eleves/{eleve_id}/entretien" in chemins
    assert "/eleves/{eleve_id}/profil" in chemins
    assert "/eleves/{eleve_id}/journal" in chemins
    assert "/eleves/{eleve_id}/point-entree" in chemins
    assert "/eleves/{eleve_id}/profil-page" in chemins
