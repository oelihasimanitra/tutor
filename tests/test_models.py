"""Tests de persistance : le schéma SQLModel reflète le DDL du livrable 2."""
from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

import app.models  # noqa: F401  (enregistre toutes les tables dans SQLModel.metadata)
from app.models import Competence, Eleve, Identite


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


def test_noms_des_tables():
    """Le schéma SQLModel doit contenir toutes les tables du livrable 2."""
    tables = set(SQLModel.metadata.tables.keys())
    attendues = {
        "eleves", "identites", "profils", "journal_profil", "competences",
        "prerequis", "gabarits_items", "items_generes", "sessions", "reponses",
        "etat_competence", "blocs_protocole", "indicateurs", "plan", "observations",
    }
    assert attendues <= tables


def test_insertion_eleve_identite_competence(engine):
    """Insertion d'un élève, de son identité et d'une compétence, avec FK."""
    with Session(engine) as s:
        eleve = Eleve(pseudonyme="el1")
        s.add(eleve)
        s.commit()
        s.refresh(eleve)
        assert eleve.id is not None

        s.add(Identite(eleve_id=eleve.id, nom="Dupont", prenom="Marie"))
        s.add(Competence(
            id="NUM.ENT.01", domaine="NUM", chapitre="Nombres entiers",
            intitule="Addition d'entiers", niveau_ref="5e", difficulte=1, type="procedure",
        ))
        s.commit()

        assert s.exec(select(Eleve)).one().pseudonyme == "el1"
        assert s.exec(select(Identite)).one().nom == "Dupont"
        assert s.exec(select(Competence)).one().intitule == "Addition d'entiers"
