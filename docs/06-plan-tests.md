# Livrable 6 — Plan de tests

Stratégie : **le moteur est 100 % pur et testé par pytest sans base ni HTTP**. Les tests de
persistance (SQLModel) vérifient le miroir du schéma. La simulation valide l'adaptatif avant tout élève
réel.

## 6.1 Tests unitaires du moteur

| Fichier | Ce qu'il vérifie |
| --- | --- |
| `test_graph.py` | Chargement YAML ; **rejet d'un graphe cyclique** ; ordre topologique ; successeurs/prérequis |
| `test_items.py` | Génération reproductible (seed) ; bornes des variables respectées ; **vérification sympy** (correct/incorrect, équivalence d'expressions `x+1` vs `1+x`) |
| `test_status.py` | Seuil de maîtrise atteint → `acquis` ; méthode incorrecte → pas acquis ; fenêtre glissante ; **propagation** vers les prérequis ; mesure l'emporte sur propagation |
| `test_selection.py` | Monte après acquisition ; descend vers un prérequis après échec ; n'atteint jamais la profondeur max ; affect élevé → item de difficulté minimale |
| `test_planner.py` | Chemin critique (prérequis avant dépendants) ; cible seule sans prérequis ; échéances J+2/J+7 relatives à l'acquisition |
| `test_indicators.py` | Taux par domaine ; progression ; calibration ; rétention |
| `test_decisions.py` | Module D : écart ≥ 2 items → gagnant ; réplication au cycle 2 → H renforcé ; sinon multimodal ; garde-fous (plaisir/fidélité/fatigue) |

## 6.2 Tests de persistance (SQLModel)

- Création des tables SQLite en mémoire ; insertion d'un élève + identité + réponse.
- Vérification que le schéma SQLModel **reflète** le DDL du livrable 2 (noms de tables/colonnes).

## 6.3 Simulation d'élèves virtuels

Profils connus injectés dans `engine/simulator.py` :

1. **« Maîtrise la chaîne »** : taux de réussite 0.9 → l'adaptatif doit monter vite, statuts `acquis`.
2. **« Lacune sur un prérequis »** : réussit tout sauf `NUM.DIV.01` → l'adaptatif doit **descendre** et
   détecter la lacune.
3. **« Élève au hasard »** : taux 0.5 → statuts `fragile`, pas de fausse maîtrise.

Critère d'acceptation : après N itérations, les statuts simulés convergent vers le profil connu
(l'adaptatif retrouve la compétence maîtrisée / la lacune), sans boucle infinie.

## 6.4 Ce qu'on ne teste pas en phase 1

- Interface HTMX et saisie navigateur (tests manuels, phase 1 outil tuteur).
- Module D réel (les règles de décision sont testées, pas le protocole complet in vivo).
- PostgreSQL réel (SQLite en test, migration Alembic à activer en phase 2).
