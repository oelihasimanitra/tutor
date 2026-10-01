# Livrable 7 — Feuille de route de la phase 1

Rappel du critère de passage de la phase 1 (SPEC §6) : *« Utilisé sur 2 ou 3 élèves réels »*.

## Tâches dans l'ordre

| # | Tâche | Estimation | Dépend de |
| --- | --- | --- | --- |
| 1 | Config YAML + chargeur (`engine/config.py`) | 0.5 j | — |
| 2 | Graphe : modèle, chargement YAML, validation d'acyclicité (`engine/graph.py`) | 1 j | 1 |
| 3 | Items : génération seedée + vérification sympy (`engine/items.py`) | 1 j | 2 |
| 4 | Statuts + propagation (`engine/status.py`) | 1 j | 2, 3 |
| 5 | Sélection adaptative (`engine/selection.py`) | 1 j | 4 |
| 6 | Planificateur + indicateurs (`engine/planner.py`, `engine/indicators.py`) | 1.5 j | 4 |
| 7 | Règles de décision + simulateur (`engine/decisions.py`, `engine/simulator.py`) | 1.5 j | 4, 5 |
| 8 | Échantillon de contenu (~25 nœuds NUM+ALG + gabarits) | 2 j | 2, 3 |
| 9 | Schéma SQLModel + import du contenu en base (`app/models/`) | 1.5 j | 2 |
| 10 | Squelette web : FastAPI + routes tuteur de saisie (`app/web/`) | 1.5 j | 9 |
| 11 | Tests unitaires + simulation (les deux verts) | 2 j | 3-7 |
| 12 | Saisie tuteur en conditions réelles sur 2-3 élèves | (itératif) | 10, 11 |

**Total estimé : ~14 j de travail**, hors itérations réelles (12) qui dépendent du terrain.

## Contenu de cette passe (déjà livré)

La présente passe couvre les tâches 1 à 11 **sauf la saisie réelle (12)** : moteur complet, schéma
SQLModel, échantillon de contenu, squelette web, et tests qui tournent. La tâche 12 est le jalon de
passage à la phase 2.

## Ordre de validation conseillé

1. Les tests moteur passent (le cœur est correct).
2. Le schéma SQLModel reflète le DDL du livrable 2.
3. La simulation converge vers les profils connus.
4. Le squelette web démarre et crée la base.

## Hors périmètre phase 1 (volontairement)

- Interface élève et PWA (phase 3).
- Module D complet in vivo (seules les règles de décision sont codées).
- `LOG.*`, éditeur de contenu, multi-tuteurs, recalibrage des seuils (phase 4).
