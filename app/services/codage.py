"""Codage des réponses brutes de l'entretien (module A).

L'entretien (``app/content/entretien.yaml``) associe chaque question à un
``champ`` de profil, un ``type_reponse`` et un ``statut`` D/M/H. Ce module
transforme un dictionnaire de réponses brutes ``{question_id: valeur}`` en un
couple ``(champs, statuts)`` directement exploitable par le profil versionné.

Le champ texte ``codage`` du YAML est de la **prose** (destinée au tuteur) : il
est interprété, pas exécuté. Les règles retenues ici :

- ``echelle_1_5`` / ``entier`` / ``observation`` : valeur numérique extraite ;
- ``booleen`` : accepte booléen ou texte (oui/non, vrai/faux, true/false, 1/0) ;
- ``choix`` : code de l'option (A-F) ; si le ``codage`` déclare une
  correspondance ``A -> jeton`` (ex. ``tendance``, ``but``), le jeton est
  retenu. ``niveau_declare`` est en outre normalisé en niveau scolaire
  (option « A: 5e » -> ``5e``, « D: 2nde » -> ``seconde``) pour pouvoir être
  comparé aux ``niveau_ref`` du graphe ;
- ``choix`` multiple : liste de codes ;
- ``texte`` : liste de valeurs (séparateurs virgule, point-virgule, retour ligne) ;
- ``autoeval[domaine]`` : dictionnaire ``{domaine: 1..5}``.

Agrégation : lorsqu'un même champ est alimenté par plusieurs questions (cas de
``anxiete`` = somme des 6 items et ``mindset`` = somme des 4 items), les valeurs
numériques sont **sommées**. Le statut retenu pour le champ est le plus fort des
statuts contributifs (M > H > D, SPEC §3.8).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ENTRETIEN_PATH = Path(__file__).resolve().parent.parent / "content" / "entretien.yaml"

# Priorité des statuts de profil (SPEC §3.8) : M l'emporte sur H, qui l'emporte sur D.
PRIORITE_STATUT = {"M": 3, "H": 2, "D": 1}

# Normalisation des niveaux déclarés vers les `niveau_ref` du graphe.
ALIAS_NIVEAU = {
    "2nde": "seconde",
    "2de": "seconde",
}

_MAPPING_RE = re.compile(r"([A-F])\s*(?:->|=>|→)\s*([A-Za-z0-9_]+)")
_ENTIER_RE = re.compile(r"-?\d+")
_SEPARATEURS_RE = re.compile(r"[;,\n]+")
_CODE_OPTION_RE = re.compile(r"^([A-F])\s*:")


def priorite_statut(statut: str | None) -> int:
    """Force relative d'un statut (M > H > D) ; inconnu = 0."""
    return PRIORITE_STATUT.get(statut or "", 0)


@lru_cache(maxsize=1)
def charger_entretien() -> dict:
    """Charge (et met en cache) le YAML de l'entretien."""
    with open(ENTRETIEN_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def structure_entretien() -> list[dict]:
    """Blocs de l'entretien (structure brute, pour le rendu du template)."""
    return charger_entretien().get("blocs", [])


@lru_cache(maxsize=1)
def _index_questions() -> dict[str, dict]:
    """Index ``question_id -> question`` (questions posées + signaux d'observation)."""
    index: dict[str, dict] = {}
    for bloc in structure_entretien():
        for question in bloc.get("questions", []):
            index[question["id"]] = question
        for signal in bloc.get("signaux", []):
            index[signal["id"]] = signal
    return index


# --- Codage d'une valeur unitaire -------------------------------------------

def _entier(brut: Any) -> int | None:
    if isinstance(brut, bool):
        return int(brut)
    if isinstance(brut, int):
        return brut
    if isinstance(brut, float):
        return int(brut)
    if isinstance(brut, str):
        trouve = _ENTIER_RE.search(brut)
        if trouve:
            return int(trouve.group())
    return None


def _booleen(brut: Any) -> bool:
    if isinstance(brut, bool):
        return brut
    if isinstance(brut, (int, float)):
        return bool(brut)
    if isinstance(brut, str):
        valeur = brut.strip().lower()
        if valeur in {"true", "vrai", "oui", "yes", "1"}:
            return True
        if valeur in {"false", "faux", "non", "no", "0"}:
            return False
    return bool(brut)


def _liste(brut: Any) -> list:
    """Découpe une réponse libre en liste (virgule, point-virgule, retour ligne)."""
    if brut is None:
        return []
    if isinstance(brut, list):
        return brut
    if isinstance(brut, str):
        return [part.strip() for part in _SEPARATEURS_RE.split(brut) if part.strip()]
    return [brut]


def _options(question: dict) -> dict[str, str]:
    """``{code: libellé}`` depuis les options « A: libellé »."""
    mapping: dict[str, str] = {}
    for option in question.get("options") or []:
        texte = str(option)
        code, separateur, libelle = texte.partition(":")
        if separateur and code.strip():
            mapping[code.strip()] = libelle.strip()
    return mapping


def _code_choix(brut: Any, options: dict[str, str]) -> str:
    """Extrait le code d'option (A, B, ...) d'une réponse brute."""
    if isinstance(brut, str):
        texte = brut.strip()
        trouve = _CODE_OPTION_RE.match(texte)
        if trouve:
            return trouve.group(1)
        if re.fullmatch(r"[A-F]", texte):
            return texte
        for code, libelle in options.items():
            if libelle.lower() == texte.lower():
                return code
        return texte
    return str(brut)


def _mapping_codage(question: dict) -> dict[str, str]:
    """Correspondances « A -> jeton » déclarées dans le texte ``codage`` du YAML."""
    return {m.group(1): m.group(2) for m in _MAPPING_RE.finditer(question.get("codage") or "")}


def _normaliser_niveau(libelle: str) -> str:
    """Normalise un niveau scolaire vers le vocabulaire des ``niveau_ref`` du graphe."""
    valeur = libelle.strip()
    return ALIAS_NIVEAU.get(valeur, valeur)


def _coder_autoeval(brut: Any) -> dict:
    """``{domaine: 1..5}`` depuis un dict ou une chaîne JSON."""
    if isinstance(brut, str):
        try:
            brut = json.loads(brut)
        except (ValueError, TypeError):
            return {}
    if isinstance(brut, dict):
        return {str(domaine): _entier(valeur) for domaine, valeur in brut.items()}
    return {}


def coder_valeur(question: dict, brut: Any) -> Any:
    """Code la réponse brute d'UNE question selon son ``type_reponse``."""
    type_reponse = question.get("type_reponse")
    champ = question.get("champ", "")

    if str(champ).startswith("autoeval"):
        return _coder_autoeval(brut)
    if type_reponse in ("echelle_1_5", "entier", "observation"):
        return _entier(brut)
    if type_reponse == "booleen":
        return _booleen(brut)
    if type_reponse == "texte":
        return _liste(brut)
    if type_reponse == "choix":
        options = _options(question)
        if question.get("multiple"):
            return [_code_choix(item, options) for item in _liste(brut)]
        mapping = _mapping_codage(question)
        code = _code_choix(brut, options)
        if code in mapping:
            return mapping[code]
        if champ == "niveau_declare" and code in options:
            return _normaliser_niveau(options[code])
        return code
    return brut


# --- Codage d'un lot de réponses --------------------------------------------

def _champ_base(champ: str) -> str:
    """``autoeval[domaine]`` -> ``autoeval``."""
    return str(champ).split("[", 1)[0]


def _agreger(valeurs: list) -> Any:
    """Combine les valeurs d'un même champ alimenté par plusieurs questions."""
    if len(valeurs) == 1:
        return valeurs[0]
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in valeurs):
        return sum(valeurs)
    if all(isinstance(v, dict) for v in valeurs):
        fusion: dict = {}
        for valeur in valeurs:
            fusion.update(valeur)
        return fusion
    return valeurs[-1]


def coder_reponses(reponses: dict[str, Any]) -> tuple[dict, dict]:
    """Transforme ``{question_id: valeur}`` en ``(champs, statuts)``.

    Les identifiants inconnus (absents du YAML versionné) sont ignorés : les ids
    de questions sont stables et versionnés sous Git.
    """
    index = _index_questions()
    valeurs_par_champ: dict[str, list] = {}
    statuts_par_champ: dict[str, list[str]] = {}

    for question_id, brut in reponses.items():
        question = index.get(question_id)
        if question is None:
            continue
        champ = _champ_base(question.get("champ", question_id))
        valeurs_par_champ.setdefault(champ, []).append(coder_valeur(question, brut))
        # Les signaux d'observation (bloc 7) n'ont pas de `statut` : ils sont mesurés.
        statuts_par_champ.setdefault(champ, []).append(question.get("statut") or "M")

    champs = {champ: _agreger(valeurs) for champ, valeurs in valeurs_par_champ.items()}
    statuts = {
        champ: max(statuts, key=priorite_statut)
        for champ, statuts in statuts_par_champ.items()
    }
    return champs, statuts
