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
import re
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any, Mapping, Sequence

import sympy
import yaml
from sympy.parsing.sympy_parser import parse_expr, standard_transformations


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
    if gabarit.format_reponse == "factorisee":
        # Une réponse factorisée est conservée telle quelle : la simplifier la
        # ré-expanderait, ce qui contredirait un énoncé « factorise ». La
        # vérification reste par équivalence (les deux formes sont acceptées).
        reponse_canonique = sympy.sstr(reponse_sym)
    else:
        reponse_canonique = sympy.sstr(sympy.simplify(reponse_sym))

    return ItemGenere(
        gabarit_id=gabarit.id,
        competence_id=gabarit.competence_id,
        variables=valeurs,
        seed=seed,
        enonce=enonce,
        reponse_attendue=reponse_canonique,
    )


# Namespace global sécurisé : les fonctions sympy (nécessaires au parse), mais
# SANS les builtins Python (``__import__``, ``open``, ``eval``…) — ce qui empêche
# toute exécution de code arbitraire saisi par le tuteur ou l'élève.
_GLOBAL_SECURISE: dict = {}
exec('from sympy import *', _GLOBAL_SECURISE)
_GLOBAL_SECURISE['__builtins__'] = {}

# Symboles et fonctions autorisés explicitement dans une réponse d'élève.
_LOCAL_SECURISE = {
    'x': sympy.Symbol('x'),
    'sqrt': sympy.sqrt,
    'floor': sympy.floor,
    'ceil': sympy.ceiling,
    'Mod': sympy.Mod,
    'Abs': sympy.Abs,
    'Min': sympy.Min,
    'Max': sympy.Max,
    'pi': sympy.pi,
    'E': sympy.E,
}

# Longueur maximale d'une réponse (garde-fou anti-DoS). Valeur de secours,
# surchargeable par la config ``seuils.verification.longueur_max``.
_LONGUEUR_MAX_PAR_DEFAUT = 200

# Multiplication implicite : "2x" -> "2*x", "2(x+1)" -> "2*(x+1)", ")x" -> ")*x".
# (``parse_expr`` ne gère pas "2x" seul dans sympy 1.14 — on l'explicite.)
_MULT_IMPLICITE = re.compile(r'(\d|\))\s*([a-zA-Z(])')


def _parser_reponse(s: str, max_longueur: int) -> sympy.Expr | None:
    """Parse une réponse élève de façon **sûre** (liste blanche, sans exécution).

    La longueur borne aussi le coût de ``simplify`` (budget anti-DoS) : une
    expression courte ne peut pas faire exploser la simplification. Un vrai
    ``timeout`` sur ``simplify`` n'est pas implémenté (hypothèse signalée).
    """
    if len(s) > max_longueur:
        return None
    s = _MULT_IMPLICITE.sub(r'\1*\2', s)
    try:
        return parse_expr(
            s,
            local_dict=_LOCAL_SECURISE,
            global_dict=_GLOBAL_SECURISE,
            transformations=standard_transformations,
        )
    except Exception:
        return None


def reponse_equivalente(
    reponse_attendue: str,
    reponse_eleve: str,
    max_longueur: int = _LONGUEUR_MAX_PAR_DEFAUT,
) -> bool:
    """Vérifie l'équivalence entre la réponse attendue et la réponse élève.

    ``x + 1`` et ``1 + x`` sont équivalentes ; ``3/6`` et ``1/2`` aussi. Une
    réponse non parsable ou malveillante est simplement incorrecte, jamais une
    exception ni une exécution de code. La réponse **attendue** est produite par
    nos gabarits (fiable) : elle reste parsée par ``sympify``.
    """
    if not reponse_eleve or not reponse_eleve.strip():
        return False

    eleve = _parser_reponse(reponse_eleve, max_longueur)
    if eleve is None:
        return False

    try:
        attendu = sympy.sympify(reponse_attendue)
    except (sympy.SympifyError, TypeError, ValueError):
        return False
    # simplify(eleve - attendu) == 0  <=> équivalence (nombres ou expressions).
    return bool(sympy.simplify(eleve - attendu) == 0)


def verifier(item: ItemGenere, reponse_eleve: str) -> bool:
    """Vérifie la réponse d'un élève par équivalence sympy (voir :func:`reponse_equivalente`)."""
    return reponse_equivalente(item.reponse_attendue, reponse_eleve)


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
