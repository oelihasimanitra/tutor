# État d'avancement

> Source de vérité pour reprendre le travail sans l'historique de session.
> Dernière mise à jour : 2026-10-01.

## Où on en est — phase 1 quasi complète

**Fait et committé (`main`) :**
- **Moteur Python pur** (`app/engine/`) : graphe (acyclicité), items (réponse calculée par sympy,
  jamais par un LLM), statuts + propagation transitive, sélection adaptative, planificateur J+2/J+7,
  indicateurs, règles de décision, simulateur d'élèves.
- **Contenu** : graphe **88 nœuds** + **182 gabarits** (NUM 100 + ALG 82, cycle 4 + seconde).
- **Entretien module A** : `app/content/entretien.yaml` (41 questions + 7 signaux d'observation).
- **Schéma SQLModel** (15 tables) + **migrations Alembic** (migration initiale en place).
- **Service de saisie** (`app/services/`) et **profil élève versionné** (entretien, journal D/M/H,
  point d'entrée déduit).
- **Interface web phase 1** : flux complet (créer élève → entretien → poser item → saisir → carte),
  accès protégé par **PIN** (`X-Tuteur-Pin`).
- **Sécurité** : évaluation des réponses via `parse_expr` en environnement restreint (anti code-exec).
- **96 tests verts**.

**Fait (2026-10-01) — revue de code traitée :** les 7 points de la revue sont corrigés et mergés dans
`main` (branche `fix/revue` conservée) : sécurité sympy, `date_acquisition` figée, `methode_correcte`,
contrôle des prérequis propagés, config/selection, robustesse des réponses, hygiène (Alembic, chemin
SQLite absolu, SPEC.md séparé).

**Reste pour boucler la phase 1 :**
1. Plan de progression exposé dans l'UI (le moteur `planner.py` est prêt et testé).
2. Tester sur 2-3 élèves réels (= critère de passage, SPEC §6).

## Décisions prises

- **ORM** : SQLModel (choix utilisateur) ; migrations Alembic en place.
- **Sécurité** : `parse_expr` restreint (pas d'`eval`), PIN via `X-Tuteur-Pin` (env `TUTORAT_PIN`,
  défaut `tutor`).
- **Contenu** : NUM + ALG, cycle 4 + seconde ; `LOG.*` reporté (module C).
- **`reaction_erreur`** (module A) : typologie A-E validée (A évitement, B persévérance,
  C recours au soutien, D inhibition, E auto-contrôle).
- **`format_reponse: "factorisee"`** : réponse non simplifiée (sinon ré-expandée) ; vérification
  par équivalence. Les 2 gabarits de factorisation existants n'utilisent pas encore ce format.
- **Moteur** : événements bruts + état dérivé ; propagation transitive des prérequis ;
  mesure > contrôle > propagation.

## Questions ouvertes

- **OQ1** : référentiel de compétences — programme officiel (Eduscol) vs référentiel perso.
- **OQ2** : entretien séquencé en YAML (à valider en usage réel).
- **UX** : ~60 lignes de JS vanilla (`TutorUI`) pour rendre le JSON en HTML, vs fragments
  serveur. À trancher sur pièce en séance.

## Dettes techniques

- Warning `httpx`/`starlette` (`TestClient`) — épingler les versions.
- Migrer les 2 gabarits de factorisation vers `format_reponse: factorisee`.
- Vérification de forme « factorisée » non implémentée (l'équivalence + traçage de méthode
  suffisent pour l'instant).
- Pilotage par l'affect (`anxiete`) non branché (seuils présents dans la config, non utilisés).

## Prochain pas (priorisé)

Exposer le **plan de progression** (`planner.py`) dans l'UI, puis **tester sur 2-3 élèves réels**
(= critère de passage de la phase 1, SPEC §6).

## Phases suivantes (SPEC §6)

- **Phase 2** : module D (protocole de représentation : carré latin, T0/T2/T7) + module C (LOG).
- **Phase 3** : interface élève, PWA, révisions espacées automatisées.
- **Phase 4** : recalibrage des seuils, éditeur de contenu, multi-tuteurs.
