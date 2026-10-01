"""Tests des items : génération seedée, bornes, vérification sympy."""
from __future__ import annotations

from app.engine.items import Gabarit, instancier, reponse_equivalente, verifier


def test_generation_reproductible(gabarits):
    """Même gabarit + même seed => même item (reproductibilité)."""
    g = gabarits["ALG.EQ1.01.i1"]
    a = instancier(g, seed=42)
    b = instancier(g, seed=42)
    assert a.enonce == b.enonce
    assert a.reponse_attendue == b.reponse_attendue
    assert a.seed == b.seed == 42


def test_variables_bornes_respectees(gabarits):
    """Les variables tirées restent dans leurs bornes sur plusieurs seeds."""
    g = gabarits["NUM.ENT.01.i1"]
    for seed in range(50):
        item = instancier(g, seed=seed)
        assert 1 <= item.variables["a"] <= 50
        assert 1 <= item.variables["b"] <= 50


def test_derive_fraction_equivalente(gabarits):
    """Les variables dérivées imposent une réponse entière et cohérente."""
    g = gabarits["NUM.FRA.02.i1"]
    for seed in range(30):
        item = instancier(g, seed=seed)
        a, b, k = item.variables["a"], item.variables["b"], item.variables["k"]
        assert item.variables["c"] == b * k
        assert item.variables["rep"] == a * k
        assert verifier(item, str(a * k))


def test_verification_equation(gabarits):
    """La solution exacte est acceptée, une valeur voisine est refusée."""
    g = gabarits["ALG.EQ1.03.i1"]
    item = instancier(g, seed=7)
    sol = item.variables["sol"]
    assert verifier(item, str(sol))
    assert not verifier(item, str(sol + 1))


def test_verification_equivalence_expression(gabarits):
    """Vérification par équivalence sympy : 3x+4x == 7x == x*7."""
    g = gabarits["ALG.LIT.02.i1"]
    item = instancier(g, seed=3)
    total = item.variables["a"] + item.variables["b"]
    assert verifier(item, f"{total}*x")
    assert verifier(item, f"x*{total}")
    assert not verifier(item, f"{total + 1}*x")


def test_equivalence_fraction():
    """1/2, 2/4 et 0.5 sont équivalents ; 1/3 ne l'est pas."""
    g = Gabarit(
        id="t", competence_id="c", type="t", difficulte=1,
        format_reponse="fraction", enonce="?", variables={}, reponse="1/2",
    )
    item = instancier(g, seed=1)
    assert verifier(item, "2/4")
    assert verifier(item, "0.5")
    assert not verifier(item, "1/3")


def test_reponse_non_parsable_refusee():
    """Une réponse non parsable (ou vide) est incorrecte, jamais une exception."""
    g = Gabarit(
        id="t", competence_id="c", type="t", difficulte=1,
        format_reponse="entier", enonce="?", variables={}, reponse="5",
    )
    item = instancier(g, seed=1)
    assert not verifier(item, "x = 5")
    assert not verifier(item, "")
    assert not verifier(item, "n'importe quoi")
    assert verifier(item, "5")


def test_instancier_seed_par_defaut_variable(gabarits):
    """Sans seed fourni, deux instanciations donnent (presque sûrement) des items différents."""
    g = gabarits["NUM.DIV.01.i1"]
    items = {instancier(g).enonce for _ in range(20)}
    assert len(items) > 1


def test_factorisation_conservee():
    """Une réponse factorisée n'est pas ré-expandée ; l'équivalence accepte les deux formes."""
    g = Gabarit(
        id="t", competence_id="c", type="factorisation", difficulte=3,
        format_reponse="factorisee", enonce="Factorise : x^2 - ${a}^2",
        variables={"a": {"min": 2, "max": 9}},
        reponse="(x - ${a})*(x + ${a})",
    )
    item = instancier(g, seed=1)
    a = item.variables["a"]
    # La réponse attendue reste factorisée (contient des parenthèses de facteurs).
    assert "(" in item.reponse_attendue
    # Les deux formes sont acceptées (équivalence), une fausse est refusée.
    assert verifier(item, f"(x - {a})*(x + {a})")
    assert verifier(item, f"x**2 - {a**2}")
    assert not verifier(item, f"x**2 - {a**2 + 1}")


def test_fraction_irreductible_exigee():
    """format_reponse "fraction" exige la forme irréductible."""
    assert reponse_equivalente("3/4", "6/8", format_reponse="fraction") is False
    assert reponse_equivalente("3/4", "3/4", format_reponse="fraction") is True
    # Sans format "fraction", l'équivalence accepte les formes équivalentes.
    assert reponse_equivalente("3/4", "6/8") is True


def test_reponse_malveillante_refusee_sans_effet_de_bord():
    """Sécurité : une saisie qui tente d'exécuter du code est refusée proprement.

    ``sympify`` passe par ``eval`` et exécuterait ``__import__('os').getcwd()``.
    On vérifie qu'une saisie malveillante renvoie ``False`` (sans exception ni
    exécution), tandis que les saisies légitimes restent acceptées.
    """
    assert not reponse_equivalente("5", "__import__('os').getcwd()")
    assert not reponse_equivalente("5", "open('secret.txt').read()")
    assert not reponse_equivalente("5", "(lambda: __import__('os').system('dir'))()")
    # Saisies légitimes : multiplication implicite, fraction, expression.
    assert reponse_equivalente("2*x", "2x")
    assert reponse_equivalente("1/2", "0.5")
    assert reponse_equivalente("x + 1", "1 + x")
    # Limite de longueur : une saisie démesurée est refusée (budget anti-DoS).
    assert not reponse_equivalente("5", "1" * 10000)
