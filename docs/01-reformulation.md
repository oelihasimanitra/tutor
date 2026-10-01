# Livrable 1 — Reformulation, hypothèses, décisions

## Reformulation (10 lignes)

Le système **assiste un tuteur — sans le remplacer** — qui suit des élèves de la 5e à la terminale en
maths + logique. Départ par un **entretien structuré** (module A) dont chaque réponse pilote un **test
adaptatif** (module B) sur un graphe de compétences à 4 niveaux (Domaine → Chapitre → Compétence →
Item) ; le module D teste **expérimentalement** la meilleure modalité de présentation (V/S/C/M, carré
latin), le module C injecte le raisonnement. Cœur technique : on stocke des **événements bruts**
(réponses, observations) et tout l'état (statuts, indicateurs, plan) est **recalculé**. Le **moteur
est un module Python pur**, découplé de l'interface web, testé avec `pytest` et validé sur des
**élèves simulés** avant le réel. Le contenu (graphe, gabarits) est **versionné sous Git** ; les
réponses des items sont **calculées par sympy**, jamais par un LLM. Phase 1 = outil tuteur de saisie ;
l'interface élève vient après. Données de mineurs : pseudonymisation, minimisation, suppression à la
demande.

## Hypothèses retenues

| # | Hypothèse | Écart au SPEC |
| --- | --- | --- |
| H1 | **ORM SQLModel** (choix utilisateur), avec Alembic pour les migrations | — |
| H2 | **SQLite d'abord, DDL portable** : types/contraintes standard uniquement (pas de `AUTOINCREMENT`/`SERIAL`). PostgreSQL = changer l'URL + une migration de types | — |
| H3 | **Front phase 1 : Jinja2 + HTMX**, serveur-side, zéro build JS | — |
| H4 | **PWA/installable repoussée en phase 3** (elle sert à l'élève, pas au tuteur de phase 1) | Oui |
| H5 | **Seuils/pondérations/règles dans `app/config/default.yaml`**, chargés par le moteur. Rien en dur | — |
| H6 | **Contenu initial** : NUM + ALG, cycle 4 (5e→3e) + seconde, échantillon ~25 nœuds (choix utilisateur). `LOG.*` reporté | — |
| H7 | **Contrôle des prérequis** : 1 item de contrôle par prérequis direct, déclenché à l'échec d'un nœud ; paramétrable | — |
| H8 | **Régénération du plan** : fin de séance + revues (4-6 sem.) + déclencheurs. Pas en continu | — |
| H9 | **Identifiants/commentaires en anglais, libellés UI + docs en français** | — |

## Points de divergence signalés (challenge)

- **P1 — « toutes les tables portent `eleve_id` » (§3.1) pris littéralement est incohérent.**
  `competences`, `prerequis`, `gabarits_items` sont du **contenu global versionné**, pas par élève.
  Lecture retenue : `eleve_id` sur toutes les tables **d'instance** uniquement.
- **P2 — « 3 sur 4 *avec méthode correcte* » (§4-B) suppose qu'on juge la méthode.** Les gabarits
  encodent donc une **procédure attendue** (champ `methode`) en plus de la réponse, faute de quoi on
  ne peut mesurer que le résultat.

## Questions ouvertes (réponses à intégrer plus tard)

- **OQ1** — Référentiel : graphe construit depuis le programme officiel (Eduscol), ou référentiel perso à injecter ?
- **OQ2** — Entretien (module A) en phase 1 : champs en base + saisie simple, ou séquencement précis des 25-30 min dès maintenant ?
