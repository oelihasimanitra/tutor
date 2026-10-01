# Suivi de tutorat — maths & logique

Assistant de suivi pour un **tuteur** (mathématiques, 5e → terminale, + entraînement à la logique).
Le tuteur reste **dans la boucle** : l'outil l'assiste, il ne le remplace pas.

La source de vérité est [SPEC.md](SPEC.md). La conception est documentée dans [docs/](docs/) (8
livrables). Le code suit l'arborescence du [livrable 3](docs/03-arborescence.md).

> **Tu arrives sur le projet ?** Commence par le
> [guide de prise en main](docs/guide-prise-en-main.md) : il explique comment ça marche sans jargon.

## Principes (résumé)

- **Événements bruts, état dérivé** : on stocke les réponses telles quelles ; statuts et indicateurs
  sont recalculés.
- **Moteur Python pur** (`app/engine/`), sans dépendance web ni BDD, testé avec `pytest`.
- **Contenu versionné** (`app/content/`) : graphe de compétences + gabarits d'items en YAML.
- **Réponses calculées par sympy**, jamais par un LLM.
- **SQLModel** pour la persistance (choix utilisateur), migrations Alembic.

## Lancer les tests

```bash
# une fois : créer l'environnement et installer
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"   # Windows
# .venv/bin/pip install -e ".[dev]"                    # macOS/Linux

# lancer la suite
.venv/Scripts/python.exe -m pytest
```

## Lancer l'API

```bash
# accès local uniquement (développement)
.venv/Scripts/python.exe -m uvicorn app.web.main:app --reload
# puis GET http://127.0.0.1:8000/health

# accès depuis une autre machine du réseau (ex. élève sur le même hotspot)
.venv/Scripts/python.exe -m uvicorn app.web.main:app --host 0.0.0.0 --port 8000
```

`0.0.0.0` écoute sur toutes les interfaces. Depuis l'autre machine, ouvrir
`http://<IP locale du PC>:8000` (IP via `ipconfig`, interface Wi-Fi). Points de
vigilance : autoriser Python dans le pare-feu Windows, désactiver l'« isolation
AP » du hotspot téléphone si elle bloque la communication entre appareils, et ne
pas laisser le serveur exposé en permanence (données d'élèves).

## Structure

```
app/engine/     moteur pédagogique (pur, testable)
app/models/     schéma SQLModel
app/services/   pont moteur ↔ persistance (import contenu, saisie tuteur)
app/content/    graphe + gabarits + entretien (versionnés)
app/config/     seuils et règles (rien en dur)
app/web/        FastAPI + Jinja2 + HTMX (phase 1)
docs/           les 8 livrables de conception
tests/          tests unitaires + simulation d'élèves virtuels
```

## État

Phase 1 en cours : moteur complet, schéma de données, contenu NUM + ALG (88 nœuds, 182 gabarits),
entretien de départ (module A), service de saisie tuteur, profil élève versionné (entretien, journal,
point d'entrée), flux web complet (élève → item → réponse → carte), accès protégé par PIN, 96 tests verts.
Prochaine étape : exposer le plan de progression dans l'UI, puis tester sur 2-3 élèves réels
(cf. [docs/07-roadmap-phase1.md](docs/07-roadmap-phase1.md)).
