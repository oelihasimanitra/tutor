"""Génération d'items à partir de gabarits + vérification des réponses via sympy.

SPEC §3.6 : items à gabarits — variables aléatoires bornées + **fonction de calcul
de la réponse**, jamais de solution produite par un LLM. Ici la « fonction de
calcul » est une **expression sympy** évaluée après substitution des variables.
La génération est **seedée** : un même gabarit + un même seed donnent exactement
le même item, ce qui rend le tout reproductible et testable.

Deux mécanismes complémentaires :
- ``variables`` : variables de base, tirées uniformément dans [min, max] ;
- ``derives`` : variables dérivées (contraintes inter-variables, ex. ``b = a * k``),
  évaluées dans l'ordre après le tirage — elles garantissent des réponses entières
  et propres pour les équations et fractions.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any, Mapping, Sequence

import sympy
import yaml


@dataclass(frozen=True)
class Gabarit:
    """Un modèle d'item paramétrable (SPEC §4-B, format du livrable 5)."""

    id: str
    competence_id: str
    type: str               # classification descriptive (documentation/statistiques)
    difficulte: int
    format_reponse: str     # entier | fraction | expression | qcm
    enonce: str             # template string.Template (${var})
    variables: Mapping[str, Mapping[str, Any]]  # {nom: {min, max, type?}}
    reponse: str            # expression sympy de la réponse
    methode: str | None = None            # procédure attendue (traçage, cf. P2)
    derives: Mapping[str, str] = field(default_factory=dict)  # {nom: expression}


@dataclass(frozen=True)
class ItemGenere:
    """Un item concret, instancié à partir d'un gabarit."""

    gabarit_id: str
    competence_id: str
    variables: Mapping[str, Any]   # valeurs tirées + dérivées
    seed: int
    enonce: str
    reponse_attendue: str          # forme canonique sympy (sstr du résultat simplifié)


def tirer_variables(gabarit: Gabarit, seed: int) -> dict[str, Any]:
    """Tire les variables bornées (RNG seedé) puis évalue les dérivées."""
    rng = random.Random(seed)
    valeurs: dict[str, Any] = {}

    for nom, spec in gabarit.variables.items():
        lo, hi = spec["min"], spec["max"]
        if spec.get("type") == "float":
            valeurs[nom] = rng.uniform(lo, hi)
        else:
            valeurs[nom] = rng.randint(int(lo), int(hi))

    # Dérivées : évaluées dans l'ordre du dict (peuvent dépendre des précédentes).
    for nom, expr in gabarit.derives.items():
        val = sympy.sympify(Template(expr).substitute(valeurs))
        valeurs[nom] = int(val) if val.is_Integer else val

    return valeurs


def instancier(gabarit: Gabarit, seed: int | None = None) -> ItemGenere:
    """Instancie un gabarit en un item concret : tirage, énoncé, réponse calculée."""
    if seed is None:
        seed = random.randrange(2**31)
    valeurs = tirer_variables(gabarit, seed)

    enonce = Template(gabarit.enonce).substitute(valeurs)
    # La réponse est *calculée* ici par sympy — jamais écrite à la main dans la base.
    reponse_sym = sympy.sympify(Template(gabarit.reponse).substitute(valeurs))
    reponse_canonique = sympy.sstr(sympy.simplify(reponse_sym))

    return ItemGenere(
        gabarit_id=gabarit.id,
        competence_id=gabarit.competence_id,
        variables=valeurs,
        seed=seed,
        enonce=enonce,
        reponse_attendue=reponse_canonique,
    )


def verifier(item: ItemGenere, reponse_eleve: str) -> bool:
    """Vérifie la réponse d'un élève par **équivalence sympy**.

    ``x + 1`` et ``1 + x`` sont équivalentes ; ``3/6`` et ``1/2`` aussi. Une
    réponse non parsable (ex. ``x = 5``) est simplement incorrecte, jamais une
    exception. On note que ``sympify`` active la multiplication implicite
    (``5x`` = ``5*x``) : la saisie du tuteur doit rester une expression sympy
    licite, ce qui est documenté côté interface.
    """
    if not reponse_eleve or not reponse_eleve.strip():
        return False
    try:
        eleve = sympy.sympify(reponse_eleve)
        attendu = sympy.sympify(item.reponse_attendue)
    except (sympy.SympifyError, TypeError, ValueError):
        return False
    # simplify(eleve - attendu) == 0  <=> équivalence (nombres ou expressions).
    return bool(sympy.simplify(eleve - attendu) == 0)


def gabarits_from_yaml(paths: Sequence[str | Path]) -> dict[str, Gabarit]:
    """Charge les gabarits depuis un ou plusieurs fichiers YAML (format livrable 5)."""
    gabarits: dict[str, Gabarit] = {}
    for path in paths:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        for d in raw["gabarits"]:
            g = Gabarit(
                id=d["id"],
                competence_id=d["competence_id"],
                type=d["type"],
                difficulte=d["difficulte"],
                format_reponse=d["format_reponse"],
                enonce=d["enonce"],
                variables=d["variables"],
                reponse=d["reponse"],
                methode=d.get("methode"),
                derives=d.get("derives", {}),
            )
            gabarits[g.id] = g
    return gabarits
