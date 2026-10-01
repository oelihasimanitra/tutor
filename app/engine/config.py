"""Chargement de la configuration (seuils, pondérations, règles de décision).

Règle d'or du SPEC (§7) : **aucun seuil ni pondération en dur dans le code**.
Tout ce qui pilote le moteur vit dans ``app/config/default.yaml``. On le charge
dans des dataclasses figées (``frozen=True``) pour qu'une clé manquante ou mal
typée échoue *au chargement*, pas en pleine séance.

Les valeurs marquées « provisoire » dans le SPEC restent éditables ici sans
toucher au code : c'est exactement le point de cette couche.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Chemin par défaut : app/config/default.yaml (parent.parent remonte de engine/ vers app/).
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.yaml"


@dataclass(frozen=True)
class SeuilMaitrise:
    """Seuil de maîtrise d'une compétence (SPEC §4-B : « 3 sur 4 avec méthode correcte »)."""

    reussites: int
    sur: int
    methode_correcte: bool


@dataclass(frozen=True)
class Retention:
    """Délais de rétention et de révision espacée (J+2 / J+7)."""

    delai_jours: int
    revision_j2: int
    revision_j7: int


@dataclass(frozen=True)
class Anxiete:
    """Seuils d'anxiété du module A (score 6 à 30) — provisoires."""

    faible_max: int
    moderee_max: int


@dataclass(frozen=True)
class Adaptatif:
    """Pilotage du test adaptatif."""

    controle_prerequis: int


@dataclass(frozen=True)
class Ponderation:
    """Poids des statuts de champ du profil (M l'emporte toujours sur D, SPEC §3.8)."""

    statut_declare: float
    statut_mesure: float
    statut_hypothese: float


@dataclass(frozen=True)
class Verification:
    """Limites de vérification des réponses saisies (anti-DoS)."""

    longueur_max: int


@dataclass(frozen=True)
class Config:
    """Configuration complète, figée après chargement."""

    seuil_maitrise: SeuilMaitrise
    retention: Retention
    anxiete: Anxiete
    adaptatif: Adaptatif
    ponderation: Ponderation
    verification: Verification

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Config":
        """Construit la Config depuis le dict YAML brut (validation par typage)."""
        s = d["seuils"]
        return cls(
            seuil_maitrise=SeuilMaitrise(**s["maitrise"]),
            retention=Retention(**s["retention"]),
            anxiete=Anxiete(**s["anxiete"]),
            adaptatif=Adaptatif(**d["adaptatif"]),
            ponderation=Ponderation(**d["ponderation"]),
            verification=Verification(**s["verification"]),
        )


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    """Charge la configuration depuis un fichier YAML."""
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return Config.from_dict(raw)
