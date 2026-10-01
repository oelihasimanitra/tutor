"""Test d'intégration minimal du squelette web (phase 1)."""
from __future__ import annotations


def test_app_route_health():
    """L'application FastAPI expose une route de santé."""
    from app.web.main import app

    routes = [r.path for r in app.routes]
    assert "/health" in routes
