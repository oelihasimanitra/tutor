# Prompt de conception — Système de suivi de tutorat (maths + logique)

**Mode d'emploi** : Tout ce qui est marqué *provisoire* doit rester configurable.

---

## 1. Rôle et mission

Tu es un architecte logiciel senior et un concepteur pédagogique. Ta mission : **concevoir** (schéma, spécifications, plan, premiers squelettes) un système de suivi pour un **tutorat individuel en mathématiques (5ème → terminale) combiné à un entraînement à la logique**, avec un objectif élève pragmatique. Tu ne codes pas tout d'un coup : tu livres la conception par étapes validables (voir §9).

## 2. Contexte

- Utilisateur principal : un **tuteur-développeur Python**, qui travaille seul au départ (quelques élèves).
- Le système doit : (a) évaluer l'élève au départ, (b) cartographier ses compétences, (c) construire un **profil d'apprentissage évolutif**, (d) produire et ajuster un plan de progression, (e) garder l'historique.
- Séances en présentiel ou visio ; le tuteur est **dans la boucle** (l'outil l'assiste, il ne le remplace pas).

## 3. Décisions déjà prises (contraintes d'architecture)

1. **Une seule base relationnelle** (SQLite au départ, PostgreSQL ensuite). Toutes les tables portent `eleve_id`. Pas de base par élève.
2. **Une seule application web** (installable, type PWA) avec **deux rôles** : tuteur et élève. **Le tuteur d'abord** : la phase 1 est un outil tuteur (saisie des résultats pendant que l'élève travaille sur papier ou au tableau). L'interface élève vient après validation du moteur.
3. **Événements bruts, état dérivé** : chaque réponse est stockée telle quelle (élève, item, réponse, temps, confiance annoncée, type d'erreur, date). Statuts de compétences et indicateurs sont **recalculables**.
4. **Moteur séparé de l'interface** : module Python pur (graphe, sélection d'items, propagation, indicateurs, planificateur, règles de décision), testable avec `pytest`.
5. **Contenu en fichiers versionnés** (YAML ou JSON sous Git) : graphe de compétences et banque d'items, importés en base.
6. **Items à gabarits** : modèle avec variables aléatoires bornées et **fonction de calcul de la réponse** (jamais de solution produite par un LLM) ; `sympy` pour vérifier l'équivalence d'expressions. Cela fournit les versions parallèles de difficulté équivalente.
7. **Élèves simulés** (profils de compétences connus) pour valider l'algorithme adaptatif avant les vrais élèves.
8. **Profil versionné** avec journal des changements et statut par champ : `D` déclaré, `M` mesuré, `H` hypothèse (`M` l'emporte toujours sur `D`).
9. **Stack suggérée** (discutable, justifie tout écart) : FastAPI, SQLAlchemy ou SQLModel, Alembic, Jinja2 + HTMX ; KaTeX (affichage) et MathLive (saisie) plus tard.
10. **Données de mineurs** : pseudonymisation (identité dans une table séparée), minimisation, sauvegardes chiffrées, suppression à la demande, consentement des familles.

## 4. Modèle pédagogique

### Module A — Entretien de départ (structuré, 25 à 30 min)

Chaque question à réponse codée remplit un champ qui **pilote** les modules suivants. Aucun champ sans usage.

| Bloc | Champs principaux | Pilote |
| --- | --- | --- |
| 1 Cible et contexte | `niveau_declare`, `tendance`, `objectif` (A rattraper, B remise à niveau puis avancer, C accélérer, D examen), `cible_niveau`, `horizon_mois`, `chapitres_vus`, `noeuds_suspects`, `priorites_log`, `drapeaux_orientation` | Point d'entrée dans le graphe, périmètre et rythme du plan |
| 2 Disponibilité | `charge_hebdo`, `duree_seance`, `creneau`, `travail_perso_min`, `supports_dispo`, `soutien` | Durée des séances, densité du plan |
| 3 Affect | `anxiete` (6 items, 6 à 30 ; seuils *provisoires* ≤ 14 faible, 15 à 21 modérée, ≥ 22 élevée), `autoeval[domaine]`, `mindset` (4 items, 4 à 20), `reaction_erreur` (A à E), `perseverance_declaree` | Difficulté des premiers items, chronomètre, ton |
| 4 Motivation | `motivation`, `but` (performance ou maîtrise), `interets`, `levier_motivation` | Contextes des problèmes, jalons |
| 5 Habitudes et préférences déclarées | `habitudes`, `preference_declaree` (statut `H`, **poids faible**), `obstacles`, `attention_declaree`, `moment_optimal` | Hypothèses à tester en module D |
| 6 Métacognition | `strategie_entree`, `verification`, `exposition_logique`, `calibration` (mesurée : confiance annoncée vs réussite) | Entraînement à la prédiction de réussite |
| 7 Observation (tuteur) | latence, abandon, auto-corrections, demandes d'indice, découragement, gestes spontanés, fatigue | Signaux comportementaux (`M`) |

Table de pilotage (exemples) : anxiété élevée → premiers items faciles, pas de chronomètre ; mindset bas → progrès chiffrés ; mauvaise calibration → exercices « prédis ta réussite » ; attention courte → blocs de 10 à 15 min ; `autoeval` ≫ niveau mesuré → travailler la lucidité d'abord.

### Module B — Test de maths adaptatif sur un graphe de compétences

- **4 niveaux** : Domaine → Chapitre → Compétence (nœud) → Item.
- **Domaines** : NUM, PRO, ALG, GEO, ESP, FON, STA, LOG.
- **Schéma d'un nœud** : `id` (ex. `ALG.EQ1.01`), `domaine`, `chapitre`, `intitule`, `niveau_ref` (indicatif), `prerequis` (arêtes **dures**), `liens_faibles`, `difficulte` (1 à 5), `type` (procédure, concept, modélisation, raisonnement), `erreurs_types`, `items`, `seuil_maitrise` (par défaut 3 sur 4 avec méthode correcte), statut par élève : absent, fragile, acquis, consolidé (rétention validée à J+7).
- **Règles** : un nœud maîtrisé présume ses prérequis acquis (vérifiés par un item de contrôle) ; un nœud échoué déclenche le test de ses prérequis directs ; départ au niveau déclaré, montée ou descente selon les résultats ; chemin critique calculé de `cible_noeuds` au statut actuel pour produire le plan.
- **Erreurs classées** : étourderie, procédure mal apprise, concept mal compris, lacune de prérequis.
- **Périmètre de départ** : 80 à 120 nœuds (NUM et ALG, cycle 4 et seconde), puis extension (250 à 400 nœuds au total).
- **Exemple de chaîne** : division euclidienne → fraction → équivalence → comparaison / addition → relatifs → expressions littérales → équations `x + a = b` → `ax = b` → `ax + b = c`.

### Module C — Logique et raisonnement

Déduction, négation, contre-exemple, motifs, détection d'une erreur de raisonnement, estimation (Fermi), problèmes ouverts à voix haute. Les nœuds `LOG.*` sont reliés aux nœuds de maths où le raisonnement intervient (Pythagore et sa réciproque, équivalence d'équations, démonstrations, récurrence).

### Module D — Protocole d'expérience de représentation

But : mesurer, **par expérience intra-élève**, quelle présentation d'une notion nouvelle donne le meilleur apprentissage durable. Les « styles d'apprentissage » (visuel, auditif, tactile) **ne sont pas considérés comme validés** : une préférence déclarée est une hypothèse faible, jamais une règle.

- **Conditions** : `V` verbale (oral + notation minimale), `S` visuelle (schémas, commentaire minimal), `C` concrète (manipulation, symboles à la fin), `M` multimodale (les trois reliées). Durée d'enseignement identique (8 min), mêmes 3 exemples travaillés et 2 exercices guidés dans toutes les conditions.
- **Notions** : nouvelles (pré-test ≤ 1 sur 3), absentes du programme scolaire en cours, faisables dans les 4 conditions, 4 notions de domaines variés et de difficulté voisine par cycle.
- **Contre-équilibrage** : carré latin 4 × 4 (VSCM / SCMV / CMVS / MVSC) ; pour un seul élève, 2 cycles avec 8 notions différentes et deux lignes différentes du carré.
- **Séquence d'un cycle** : J0 (pré-tests + enseignement et T0 de N1, N2), J+2 (T2 de N1, N2 + enseignement et T0 de N3, N4), J+4 (T2 de N3, N4), J+7 (T7 de N1, N2), J+9 (T7 de N3, N4 + réenseignement). Tolérance ±1 jour, intervalles J+2 et J+7 respectés par notion.
- **Tests** : pré-test P (3 items), T0, T2, T7 (chacun 6 items = 4 « proches » + 2 « transfert »), 4 versions parallèles par notion. Aucune aide pendant T0, **aucune correction entre T2 et T7**, aucun devoir sur ces notions ; réenseignement après T7.
- **Mesures par notion** : scores `pre`, `T0`, `T2`, `T7` (proche et transfert), temps moyen, type d'erreur, `effort` (1 à 5), `plaisir` (1 à 5), `engagement` (0 à 6 : attention, initiative, affect, 0 à 2 chacun), fatigue (1 à 3), fiche de fidélité du tuteur (5 cases).
- **Indicateurs** : gain normalisé `g = (T0_p − pre_p) / (1 − pre_p)` ; rétention `R7 = T7_p / T0_p` ; transfert `Tr = (T0_transfert + T7_transfert) / 4` ; écart plaisir-efficacité. **Critère principal : `T7_p`.**
- **Règles de décision (provisoires, configurables)** : une condition est favorable si elle dépasse les autres d'**au moins 2 items sur 6** en `T7_p` **et** que l'ordre se retrouve au cycle 2 → `representation_efficace` (statut `H` renforcé). Écart au cycle 1 seulement → `H` faible. Aucun écart → **rester multimodal**. Si `M` ≥ meilleure condition simple → multimodal. Plaisir élevé mais `T7_p` bas → modalité utile pour motiver, pas pour installer. Blocs à fidélité douteuse ou fatigue forte → exclus ou refaits.

### Profil élève vivant

Champs des modules A à D + `representation_efficace` + écart déclaré/mesuré. **Déclencheurs de révision** : écart entre niveau prédit et observé sur un bloc, stagnation sur 2 à 3 séances, changement d'objectif ou de contraintes, rétention insuffisante à J+7, fin de bloc ; revue toutes les 4 à 6 semaines. Chaque modification = nouvelle version (date, champ, ancienne et nouvelle valeur, raison). Précaution : profil **pédagogique, pas diagnostic** ; si difficultés marquées et persistantes (`drapeaux_orientation`), orienter la famille vers un professionnel.

## 5. Entités de données à modéliser

`eleves` (pseudonyme) + `identites` (table séparée) · `profils` (versionné) + `journal_profil` · `competences` · `prerequis` (arêtes dures ou faibles) · `gabarits_items` et `items_generes` · `sessions` · `reponses` (événements bruts) · `etat_competence` (dérivé) · `blocs_protocole` (notion, condition, ordre, tests, mesures, fidélité) · `observations` (grille) · `indicateurs` (dérivés, recalculables) · `plan` (nœuds cibles, ordre, échéances).

## 6. Phasage

| Phase | Contenu | Critère de passage |
| --- | --- | --- |
| 0 | Schéma de base, graphe v1 (NUM et ALG cycle 4), gabarits d'items | Graphe cohérent, sans cycles |
| 1 | Outil tuteur : entretien, saisie des résultats, carte de compétences, journal du profil | Utilisé sur 2 ou 3 élèves réels |
| 2 | Test adaptatif semi-automatique et protocole de représentation (planning, calculs) | Résultats cohérents avec le jugement du tuteur |
| 3 | Application élève : séances guidées, exercices, révisions espacées | Usage autonome sans blocage |
| 4 | Analyses, recalibrage des seuils, éditeur de contenu, multi-tuteurs | Seuils fondés sur des données réelles |

## 7. Contraintes de conception

- Pas de sur-ingénierie : MVP = phase 1. Privilégie la simplicité et la réversibilité (migrations Alembic).
- Tous les seuils et pondérations sont **dans la configuration**, pas dans le code.
- Les solutions des items sont **calculées par code**, jamais générées par un modèle de langage.
- Code et identifiants en anglais ; documentation, interface et libellés en français.
- Signale toute incertitude, toute hypothèse et tout compromis plutôt que de trancher en silence.

## 8. Ce que je ne veux pas

- Une base de données par élève.
- Deux applications séparées dès le départ.
- Une classification de l'élève en « type visuel, auditif ou tactile » sur la seule foi d'un questionnaire.
- Des seuils figés en dur.

## 9. Livrables attendus, dans cet ordre (valide chacun avec moi avant le suivant)

1. **Reformulation** de ta compréhension en 10 lignes maximum + **liste de questions ouvertes** (5 maximum) + hypothèses retenues.
2. **Schéma de données** : DDL SQL compatible SQLite et PostgreSQL + diagramme entité-relation (Mermaid).
3. **Arborescence du projet** et découpage en modules (moteur, API, interface, contenu, tests).
4. **Spécification du moteur** en pseudo-code : sélection du prochain item, propagation des prérequis, mise à jour des statuts, planificateur J+2 et J+7, calcul des indicateurs, règles de décision, avec cas limites.
5. **Formats des fichiers de contenu** (YAML du graphe, YAML des gabarits d'items), avec 5 nœuds et 2 gabarits d'exemple.
6. **Plan de tests** : unitaires du moteur et simulation d'élèves virtuels.
7. **Feuille de route détaillée** de la phase 1 (tâches, estimation, ordre).
8. **Risques et alternatives** (stack, hébergement, sécurité, charge de saisie du tuteur).

**Commence par le livrable 1.**