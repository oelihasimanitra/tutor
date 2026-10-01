# Livrable 3 — Arborescence du projet et découpage en modules

Principe : **moteur = Python pur** (aucune dépendance web/BDD à l'import), séparé de l'interface et des
modèles. Le moteur manipule des structures en mémoire (graphe, réponses), pas des lignes SQL : il est
ainsi testable sans base.

```
projet-tutorat/
├── SPEC.md                     # le prompt de conception (source de vérité)
├── pyproject.toml              # dépendances + config pytest
├── .gitignore
├── docs/                       # les 8 livrables de conception (ce dossier)
│   ├── 01-reformulation.md
│   ├── 02-schema-donnees.md
│   ├── 03-arborescence.md
│   ├── 04-spec-moteur.md
│   ├── 05-formats-contenu.md
│   ├── 06-plan-tests.md
│   ├── 07-roadmap-phase1.md
│   └── 08-risques-alternatives.md
├── app/
│   ├── config/
│   │   └── default.yaml        # seuils, pondérations, règles (rien en dur)
│   ├── content/                # contenu VERSIONNÉ sous Git (importé en base)
│   │   ├── graph/
│   │   │   └── num_alg.yaml    # graphe NUM + ALG (échantillon ~25 nœuds)
│   │   └── items/
│   │       ├── num.yaml        # gabarits d'items NUM
│   │       └── alg.yaml        # gabarits d'items ALG
│   ├── engine/                 # MOTEUR (Python pur, testé par pytest)
│   │   ├── __init__.py
│   │   ├── config.py           # chargement de la config YAML (dataclass figée)
│   │   ├── graph.py            # graphe : chargement YAML + validation d'acyclicité
│   │   ├── items.py            # génération d'items + vérification sympy
│   │   ├── status.py           # statuts de compétence + propagation des prérequis
│   │   ├── selection.py        # choix du prochain item (adaptatif)
│   │   ├── indicators.py       # indicateurs dérivés
│   │   ├── planner.py          # planificateur (chemin critique, J+2 / J+7)
│   │   ├── decisions.py        # règles de décision (module D + pilotage)
│   │   └── simulator.py        # élèves simulés (validation de l'adaptatif)
│   ├── models/                 # schéma SQLModel (persistance)
│   │   ├── __init__.py
│   │   ├── base.py             # base commune (id, engine)
│   │   ├── eleve.py            # Eleve, Identite
│   │   ├── profil.py           # Profil, JournalProfil
│   │   ├── competence.py       # Competence, Prerequis
│   │   ├── item.py             # GabaritItem, ItemGenere
│   │   ├── session.py          # Session, Reponse, Observation
│   │   ├── etat.py             # EtatCompetence
│   │   ├── protocole.py        # BlocProtocole
│   │   └── plan.py             # Plan, Indicateur
│   └── web/                    # FastAPI + Jinja2 + HTMX (phase 1)
│       ├── __init__.py
│       ├── main.py             # app FastAPI (squelette phase 1)
│       └── db.py               # engine SQLite + création des tables
└── tests/
    ├── conftest.py             # fixtures partagées (config, graphe de test)
    ├── test_graph.py           # acyclicité, chargement
    ├── test_items.py           # génération, vérification sympy
    ├── test_status.py          # statuts + propagation
    ├── test_selection.py       # sélection adaptative
    ├── test_planner.py         # chemin critique, J+2 / J+7
    ├── test_indicators.py      # indicateurs dérivés
    └── test_simulation.py      # élève simulé (boucle adaptative complète)
```

## Rôles et dépendances

| Module | Responsabilité | Dépend de |
| --- | --- | --- |
| `engine.config` | Charge `default.yaml`, expose une structure figée | pyyaml |
| `engine.graph` | Charge le graphe YAML, expose `successeurs`/`prerequis`, **valide l'acyclicité** | `config` |
| `engine.items` | Instancie un gabarit (tirage seedé), calcule la réponse via **sympy**, vérifie une réponse élève | `graph`, sympy |
| `engine.status` | Calcule le statut d'une compétence et **propage** vers les prérequis | `graph`, `config` |
| `engine.selection` | Choisit le prochain item (adaptatif : monte/descend selon résultats) | `graph`, `status` |
| `engine.indicators` | Recalcule les indicateurs depuis les réponses brutes | — |
| `engine.planner` | Produit le plan ordonné + échéances J+2/J+7 | `graph`, `status` |
| `engine.decisions` | Applique les règles de décision (module D + pilotage par l'affect) | `config` |
| `engine.simulator` | Génère des réponses synthétiques d'élèves aux profils connus | `items` |
| `models.*` | Persistance SQLModel (miroir du schéma livrable 2) | sqlmodel |
| `web.*` | FastAPI + Jinja2 + HTMX (phase 1, squelette) | `models`, `engine` |

## Invariants

1. Le moteur n'importe **jamais** `models` ni `web` (pas de couplage à la BDD ni à HTTP).
2. Le moteur ne lit **aucun seuil en dur** : tout vient de `config`.
3. Le contenu (`content/`) n'est pas du code : il est chargé puis importé en base.
