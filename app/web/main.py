"""Application FastAPI — phase 1 (outil tuteur).

Au démarrage, on charge le contenu versionné (graphe + gabarits) et la config,
on importe le contenu en base (idempotent), puis on expose le tout dans
``app.state`` pour que les routes puissent construire un ``TuteurService`` par
requête (une session SQLModel n'est pas thread-safe, donc on n'en partage pas).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlmodel import Session

from app.engine.config import load_config
from app.engine.content import charger_contenu
from app.services.importer import importer_contenu

from .db import engine, init_db
from .routes.tuteur import router as tuteur_router

# Racine du projet (app/web/main.py -> 3 niveaux au-dessus).
ROOT = Path(__file__).resolve().parent.parent.parent
GRAPH_PATH = ROOT / "app" / "content" / "graph" / "num_alg.yaml"
ITEMS_PATHS = [
    ROOT / "app" / "content" / "items" / "num.yaml",
    ROOT / "app" / "content" / "items" / "alg.yaml",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Tables de la base (idempotent).
    init_db()
    # 2. Charger contenu + config, et importer le contenu en base.
    config = load_config()
    graphe, gabarits = charger_contenu(GRAPH_PATH, ITEMS_PATHS)
    with Session(engine) as session:
        importer_contenu(graphe, gabarits, session)
    # 3. Exposer l'état aux routes via app.state.
    app.state.engine = engine
    app.state.config = config
    app.state.graphe = graphe
    app.state.gabarits = gabarits
    yield


app = FastAPI(title="Suivi de tutorat — maths & logique", lifespan=lifespan)

# Routes de saisie tuteur (API JSON + pages Jinja2) — cf. app/web/routes/tuteur.py.
app.include_router(tuteur_router)


@app.get("/health")
def health() -> dict:
    """Route de santé : confirme que l'API répond."""
    return {"statut": "ok", "message": "Le service de suivi de tutorat répond."}
