"""Application FastAPI (squelette phase 1).

Phase 1 = outil tuteur. Ce squelette expose une route de santé et initialise la
base. Les routes de saisie tuteur (entretien, réponses) arrivent dans la foulée
— voir docs/07-roadmap-phase1.md, tâche 10.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crée les tables au démarrage du serveur."""
    init_db()
    yield


app = FastAPI(title="Suivi de tutorat — maths & logique", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    """Route de santé : confirme que l'API répond."""
    return {"statut": "ok", "message": "Le service de suivi de tutorat répond."}
