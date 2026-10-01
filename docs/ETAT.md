# État d'avancement

> Source de vérité pour reprendre le travail sans l'historique de session.
> Dernière mise à jour : 2026-10-01.

## Où on en est — phase 1 quasi complète

**Fait et committé (4 commits, `main`) :**
- **Moteur Python pur** (`app/engine/`) : graphe (acyclicité), items (sympy), statuts +
  propagation transitive, sélection adaptative, planificateur J+2/J+7, indicateurs,
  règles de décision, simulateur d'élèves.
- **Contenu** : graphe **88 nœuds** + **91 gabarits** (NUM + ALG, cycle 4 + seconde).
- **Entretien module A** : `app/content/entretien.yaml` (41 questions + 7 signaux d'observation).
- **Schéma SQLModel** (15 tables), **service de saisie** (`app/services/`).
- **Interface web phase 1** : 4 endpoints API + pages HTMX (index, saisie, carte), flux
  complet validé (créer élève → poser item → saisir → carte).
- **84 tests verts**.

**Fait (2026-10-01) — le chaînon « profil » est bouclé :**
1. Saisie de l'entretien dans l'UI (`entretien.html`) → alimente le profil.
2. Profil vivant + journal (`app/services/profil.py`) : versionné, D/M/H, « M l'emporte sur D ».
3. Point d'entrée déduit (`niveau_declare` / `noeuds_suspects` → nœud du graphe).

**Reste pour boucler la phase 1 :**
4. Plan de progression exposé (le moteur `planner.py` est prêt et testé).
5. Tester sur 2-3 élèves réels (= critère de passage, SPEC §6).

## Décisions prises

- **ORM** : SQLModel (choix utilisateur) ; Alembic à configurer quand le schéma évoluera.
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
- Alembic (migrations) à mettre en place.

## Prochain pas (priorisé)

Exposer le **plan de progression** (`planner.py`) dans l'UI, puis **tester sur 2-3 élèves réels**
(= critère de passage de la phase 1, SPEC §6).

## Phases suivantes (SPEC §6)

- **Phase 2** : module D (protocole de représentation : carré latin, T0/T2/T7) + module C (LOG).
- **Phase 3** : interface élève, PWA, révisions espacées automatisées.
- **Phase 4** : recalibrage des seuils, éditeur de contenu, multi-tuteurs.
