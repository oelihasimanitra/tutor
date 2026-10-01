"""Authentification minimale du tuteur (PIN).

Le PIN protège toutes les routes de saisie (sauf ``/health``). Il se lit depuis
la variable d'environnement ``TUTORAT_PIN``, avec un PIN de développement par
défaut. Hypothèse : un **secret** vit dans l'environnement, pas dans la config
versionnée — contrairement aux seuils pédagogiques qui, eux, sont dans
``app/config/default.yaml``.
"""
from __future__ import annotations

import os

from fastapi import Header, HTTPException

# PIN de développement. À surcharger en production via TUTORAT_PIN.
_PIN_PAR_DEFAUT = "tutor"


def verifier_pin(x_tuteur_pin: str | None = Header(default=None)) -> None:
    """Dépendance FastAPI : exige le PIN tuteur via l'en-tête ``X-Tuteur-Pin``."""
    pin_attendu = os.environ.get("TUTORAT_PIN", _PIN_PAR_DEFAUT)
    if x_tuteur_pin != pin_attendu:
        raise HTTPException(status_code=401, detail="PIN tuteur manquant ou invalide.")
