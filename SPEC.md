# Spécification — Système de suivi de tutorat (maths + logique)

Spécification stable du projet. Le prompt de conception initial est archivé dans
[docs/prompt-conception.md](docs/prompt-conception.md) ; l'état d'avancement est
dans [docs/ETAT.md](docs/ETAT.md).

## Objectif

Assister un tuteur (sans le remplacer) qui suit des élèves de la 5e à la terminale
en maths + logique : évaluer, cartographier les compétences, construire un profil
vivant, produire un plan de progression, garder l'historique.

## Architecture (décisions)

- Une seule base relationnelle (SQLite puis PostgreSQL) ; toutes les tables
  d'instance portent `eleve_id`.
- Une seule application web (FastAPI + Jinja2 + HTMX) ; le tuteur d'abord.
- **Événements bruts, état dérivé** : réponses stockées telles quelles, statuts
  et indicateurs recalculés.
- **Moteur Python pur** (`app/engine/`), séparé de l'interface, testé avec pytest.
- **Contenu versionné** (YAML sous Git) : graphe de compétences + gabarits d'items.
- **Réponses calculées par sympy** (jamais par un LLM) ; items à gabarits.
- **SQLModel** pour la persistance ; Alembic pour les migrations.
- **Profil versionné** avec journal (statut D/M/H ; M l'emporte sur D).

## Modèle pédagogique

- **Module A** — entretien de départ structuré (alimente le profil).
- **Module B** — test adaptatif sur un graphe de compétences (Domaine → Chapitre
  → Compétence → Item), 4 statuts (absent, fragile, acquis, consolidé).
- **Module C** — logique et raisonnement (reporté).
- **Module D** — protocole d'expérience de représentation (V/S/C/M, carré latin).

## Entités

`eleves` + `identites` · `profils` + `journal_profil` · `competences` + `prerequis`
· `gabarits_items` + `items_generes` · `sessions` · `reponses` · `etat_competence`
· `blocs_protocole` · `observations` · `indicateurs` · `plan`.

## Règles clés

- Seuils et pondérations dans `app/config/default.yaml` (rien en dur).
- Un nœud maîtrisé présume ses prérequis acquis (vérifiés par un item de contrôle).
- Contenu de départ : NUM + ALG, cycle 4 (5e → 3e) + seconde.
- Données de mineurs : pseudonymisation, minimisation, suppression à la demande.

## Détail

- Schéma de données : [docs/02-schema-donnees.md](docs/02-schema-donnees.md)
- Moteur : [docs/04-spec-moteur.md](docs/04-spec-moteur.md)
- Formats de contenu : [docs/05-formats-contenu.md](docs/05-formats-contenu.md)
- Feuille de route : [docs/07-roadmap-phase1.md](docs/07-roadmap-phase1.md)
