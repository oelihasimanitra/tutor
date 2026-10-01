# Suivi de tutorat — maths & logique

Assistant de suivi pour un **tuteur** (mathématiques, 5e → terminale, + entraînement à la logique).
Le tuteur reste **dans la boucle** : l'outil l'assiste, il ne le remplace pas.

La source de vérité est [SPEC.md](SPEC.md). La conception est documentée dans [docs/](docs/) (8
livrables). Le code suit l'arborescence du [livrable 3](docs/03-arborescence.md).

## Principes (résumé)

- **Événements bruts, état dérivé** : on stocke les réponses telles quelles ; statuts et indicateurs
  sont recalculés.
- **Moteur Python pur** (`app/engine/`), sans dépendance web ni BDD, testé avec `pytest`.
- **Contenu versionné** (`app/content/`) : graphe de compétences + gabarits d'items en YAML.
- **Réponses calculées par sympy**, jamais par un LLM.
- **SQLModel** pour la persistance (choix utilisateur), Alembic à venir pour les migrations.

## Lancer les tests

```bash
# une fois : créer l'environnement et installer
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"   # Windows
# .venv/bin/pip install -e ".[dev]"                    # macOS/Linux

# lancer la suite
.venv/Scripts/python.exe -m pytest
```

## Lancer l'API (squelette phase 1)

```bash
.venv/Scripts/python.exe -m uvicorn app.web.main:app --reload
# puis GET http://127.0.0.1:8000/health
```

## Structure

```
app/engine/     moteur pédagogique (pur, testable)
app/models/     schéma SQLModel
app/content/    graphe + gabarits (versionnés)
app/config/     seuils et pondérations (rien en dur)
app/web/        FastAPI + Jinja2 + HTMX (phase 1)
docs/           les 8 livrables de conception
tests/          tests unitaires + simulation d'élèves virtuels
```

## État

Phase 1 en cours : moteur complet, schéma de données, échantillon de contenu (25 nœuds NUM + ALG),
squelette web, tests verts. Prochaine étape : saisie tuteur sur 2-3 élèves réels
(cf. [docs/07-roadmap-phase1.md](docs/07-roadmap-phase1.md)).
