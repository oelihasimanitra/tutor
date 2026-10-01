"""Tests du service de saisie tuteur (pont moteur ↔ persistance)."""
from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

import app.models  # noqa: F401  (enregistre les tables)
from app.models import Competence, GabaritItem, ItemGenere, Prerequis, Reponse
from app.services.importer import importer_contenu
from app.services.tuteur import TuteurService


@pytest.fixture
def engine():
    """Base SQLite en mémoire, partagée via StaticPool."""
    e = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(e)
    return e


def _service(engine, graphe, gabarits, config) -> TuteurService:
    """Construit un service sur une session fraîche."""
    session = Session(engine)
    return session, TuteurService(session, graphe, gabarits, config)


def test_import_contenu(engine, graphe, gabarits):
    """L'import persiste compétences, prérequis et gabarits dans les bonnes tables."""
    with Session(engine) as s:
        compteur = importer_contenu(graphe, gabarits, s)
        assert compteur["competences"] == len(graphe)
        assert compteur["gabarits"] == len(gabarits)
        assert compteur["prerequis"] > 0
        assert s.exec(select(Competence)).first() is not None
        assert s.exec(select(GabaritItem)).first() is not None
        assert s.exec(select(Prerequis)).first() is not None


def test_saisie_bonne_reponse_acquisition(engine, graphe, gabarits, config):
    """3 bonnes réponses sur un nœud => la carte le déclare acquis."""
    session, service = _service(engine, graphe, gabarits, config)
    with session:
        eleve = service.creer_eleve("el1")

        item_db = service.prochain_item(eleve.id, "NUM.ENT.01")
        assert item_db is not None
        assert item_db.gabarit_id == "NUM.ENT.01.i1"

        for _ in range(3):
            service.enregistrer_reponse(eleve.id, item_db, item_db.reponse_attendue)

        carte = service.carte_competences(eleve.id)
        assert carte["NUM.ENT.01"].statut.value == "acquis"


def test_saisie_mauvaise_reponse(engine, graphe, gabarits, config):
    """Une mauvaise réponse est enregistrée avec est_correct=False."""
    session, service = _service(engine, graphe, gabarits, config)
    with session:
        eleve = service.creer_eleve("el2")
        item_db = service.prochain_item(eleve.id, "NUM.ENT.01")
        rep = service.enregistrer_reponse(eleve.id, item_db, "999999")
        assert rep.est_correct is False
        # la réponse est bien liée à l'item généré (traçabilité)
        assert rep.item_id == item_db.id
        assert rep.competence_id == "NUM.ENT.01"


def test_item_genere_persiste_et_lie(engine, graphe, gabarits, config):
    """L'item généré est persisté, et la réponse y fait référence."""
    session, service = _service(engine, graphe, gabarits, config)
    with session:
        eleve = service.creer_eleve("el3")
        item_db = service.prochain_item(eleve.id, "NUM.ENT.01")
        assert item_db.id is not None
        stored = session.get(ItemGenere, item_db.id)
        assert stored is not None
        assert stored.reponse_attendue == item_db.reponse_attendue
