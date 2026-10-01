"""Test d'intégration minimal du squelette web (phase 1)."""
from __future__ import annotations


def test_app_route_health():
    """L'application FastAPI expose une route de santé."""
    from app.web.main import app

    # FastAPI inclut les routers de façon paresseuse (objet _IncludedRouter sans .path).
    routes = [getattr(r, "path", None) for r in app.routes]
    assert "/health" in routes
