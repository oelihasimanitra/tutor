# Livrable 8 — Risques et alternatives

## Risques

| # | Risque | Impact | Mitigation |
| --- | --- | --- | --- |
| R1 | **Charge de saisie du tuteur** trop lourde en séance (frein n°1 à l'adoption) | Abandon de l'outil | Saisie minimale (une touche par réponse), pré-remplissage, saisie différée possible après séance |
| R2 | **Graphe de compétences trop fin ou trop grossier** → l'adaptatif dérive | Mauvaise évaluation | Échantillon d'abord ; granularité ajustable ; le contenu est versionné, donc re-tunable sans code |
| R3 | **Seuils provisoires faux** (anxiété, maîtrise 3/4) | Décisions biaisées | Tout dans la config ; recalibrage en phase 4 sur données réelles |
| R4 | **SQLite → PostgreSQL** mal anticipé | Migration douloureuse | DDL volontairement portable dès le départ + Alembic |
| R5 | **Données de mineurs** (RGPD) | Risque légal | `identites` séparée, minimisation, suppression à la demande, sauvegardes chiffrées |
| R6 | **Module D complexe** (carré latin, J+2/J+7) | Surcharge de la phase 1 | Réduit à ses règles de décision en phase 1 ; le protocole complet en phase 2 |
| R7 | **Sur-ingénierie** | Perte de temps | MVP strictement borné à la phase 1 ; le moteur reste un module pur |

## Alternatives considérées

| Choix | Alternative écartée | Pourquoi |
| --- | --- | --- |
| SQLModel | SQLAlchemy brut | SQLModel = SQLAlchemy + Pydantic : moins de code de glue, validation intégrée ; choisi par le tuteur |
| Jinja2 + HTMX | SPA (React/Vue) | Un seul dev, pas de build JS, HTMX suffit pour des formulaires de saisie |
| Moteur pur | Moteur couplé à FastAPI/BDD | Testabilité et réversibilité ; le moteur doit pouvoir changer d'interface |
| Événements bruts + état dérivé | État stocké directement | Recalculabilité, audit, correction de bugs rétroactive |
| sympy pour les réponses | Réponses statiques ou LLM | Reproductible, exact, jamais de solution hallucinée (SPEC §7) |
| SQLite au départ | PostgreSQL d'emblée | Zéro infra pour un tuteur seul ; migration planifiée |
