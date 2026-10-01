# Guide de prise en main — Suivi de tutorat (maths & logique)

> Ce guide s'adresse à **celui ou celle qui arrive et veut comprendre comment ça marche**,
> sans entrer dans le code. Il ne remplace pas la documentation : il te donne les clés de
> lecture, puis te renvoie vers les documents techniques quand tu auras besoin d'aller plus loin.
>
> Pour les détails techniques : [SPEC.md](../SPEC.md) (la source de vérité), [README](../README.md)
> (installer/lancer) et [docs/](.) (les 8 livrables de conception).

---

## En deux mots

C'est un **outil d'aide au tuteur** qui suit des élèves de la 5e à la terminale en mathématiques
(et plus tard en logique).

Le point important, à garder en tête en permanence : **l'outil assiste, il ne remplace pas le tuteur.**
Tu restes aux commandes. L'outil te prépare le travail (quel exercice poser, où en est l'élève, quoi
réviser), mais c'est toi qui fais cours, qui observes l'élève, qui juges la méthode.

Ce que fait l'outil :

- il connaît une **carte des compétences** (ce qu'il faut savoir, dans quel ordre) ;
- il te propose le **bon exercice au bon moment**, en s'adaptant au niveau de l'élève ;
- il **calcule lui-même les réponses** des exercices (jamais de « devinette » par une IA, donc toujours justes) ;
- il **mémorise** chaque réponse et en tire un **état** clair de l'élève.

---

## Le vocabulaire en clair

Voici les mots que tu vas croiser partout, traduits sans jargon.

| Mot | Ce que ça veut dire |
|---|---|
| **Élève** | La personne que tu suis. On l'enregistre avec un **pseudonyme** (pas son vrai nom), pour protéger ses données. |
| **Compétence** | Un savoir-faire précis, ex. « résoudre une équation du premier degré ». |
| **Item** (ou **exercice**) | Une question posée à l'élève. |
| **Gabarit** | Le « moule » d'un exercice. À chaque pose, le programme tire des **nombres différents**, donc l'élève ne retombe pas sur le même exercice. |
| **Statut** | Où en est l'élève sur une compétence (voir « Les 4 statuts » plus bas). |
| **Prérequis** | Une compétence qu'il faut maîtriser **avant** d'en aborder une autre. |
| **Propagation** | Si l'élève maîtrise une compétence, on suppose qu'il en maîtrise les prérequis. C'est une **supposition**, pas une mesure. |
| **Item de contrôle** | Un petit test posé pour **confirmer** cette supposition. |
| **Carte des compétences** | La vue d'ensemble colorée : où en est l'élève sur chaque compétence. |
| **Plan de progression** | La liste ordonnée de ce qu'il reste à travailler, avec les révisions à venir. |
| **Profil** | La fiche de l'élève : niveau, rapport aux maths, points d'attention. Elle est **versionnée** (on garde l'historique des changements). |

---

## Les 4 statuts

Chaque compétence a un statut, visible sur la carte. C'est le cœur de la lecture.

| Statut | Ce que ça veut dire pour toi |
|---|---|
| **Absent** | Pas encore vu, pas encore testé. Rien à dire pour l'instant. |
| **Fragile** | L'élève a essayé, mais ça ne tient pas encore. C'est là qu'il faut travailler. |
| **Acquis** | Il réussit, avec la bonne méthode. |
| **Consolidé** | Il réussit **encore après un délai** : ça tient dans le temps, pas seulement sur l'instant. |

Deux règles simples à retenir :

- **La mesure directe l'emporte toujours sur une supposition.** Si on a *supposé* une compétence
  acquise (propagation), un item de contrôle vient la confirmer ou la casser.
- Les seuils (combien de réussites pour « acquis », combien de temps avant « consolidé »…) sont
  **réglables dans un fichier de configuration**, sans toucher au programme.

---

## Ce que tu vois à l'écran

L'outil s'ouvre dans un navigateur (c'est une page web). Les écrans principaux :

- **Accueil** : la liste des élèves, et le bouton pour en créer un.
- **Fiche élève** : l'espace de saisie — c'est là que tu poses un exercice et que tu enregistres la réponse.
- **Entretien** : le questionnaire de départ (module A), pour situer l'élève.
- **Carte des compétences** : l'état de l'élève, compétence par compétence.
- **Profil** : la fiche vivante de l'élève, avec son historique.

L'accès est protégé par un **code simple** (un PIN, « tutor » par défaut) que le développeur peut changer.

---

## Une séance type, pas à pas

1. **Ouvre l'outil** et choisis l'élève (ou crée-le, avec un pseudonyme).
2. **Première séance** : fais l'**entretien de départ** — il sert de point d'entrée.
3. L'outil te propose le **prochain exercice** (le bon nœud, au bon niveau).
4. L'élève répond. **Tu saisis sa réponse**, et ce que tu as observé (la méthode, sa confiance, l'erreur éventuelle).
5. L'outil **vérifie la réponse** (il a calculé la bonne réponse lui-même) et met à jour les statuts.
6. Regarde la **carte** : elle reflète aussitôt ce qui vient de se passer.
7. **Fin de séance** : le plan de progression se met à jour (quoi travailler ensuite, quoi réviser à J+2 et J+7).

En clair : tu poses l'exercice que l'outil te suggère, tu saisis ce que tu vois, et la carte se met à jour toute seule.

---

## Comment l'outil décide quoi poser

Sans entrer dans le code, voici la logique du moteur (le cerveau de l'outil) :

- On part du **point d'entrée** de l'élève (son niveau déclaré à l'entretien).
- S'il **maîtrise** la compétence courante → on **monte** vers ce qu'il ne maîtrise pas encore.
- S'il est **fragile** ou qu'il lui manque des **prérequis** → on **descend** vers le prérequis qui manque.
- Sinon → on pose un **exercice de cette compétence**, avec des valeurs différentes de la fois précédente.
- Quand on a *supposé* un prérequis acquis, on le **confirme** par un item de contrôle.

Les exercices existent en **plusieurs niveaux de difficulté** et se **renouvellent** à chaque pose :
l'élève s'entraîne sans faire toujours la même chose.

---

## Les 4 modules (A, B, C, D)

Le projet est découpé en quatre grandes fonctions, que tu croiseras dans la doc :

- **Module A — Entretien** : faire connaissance avec l'élève (niveau, affect, rapport aux maths).
- **Module B — Test adaptatif** : la sélection des exercices qui s'ajuste au niveau. C'est le cœur de la phase actuelle.
- **Module C — Logique** : l'entraînement au raisonnement. *(reporté, viendra plus tard)*
- **Module D — Représentation** : tester **expérimentalement** la meilleure façon de présenter les exercices (visuel, symbolique, concret, multimodal). *(viendra plus tard)*

---

## Pour démarrer

> La toute première fois, fais-toi aider par le développeur : c'est une installation unique,
> puis ça devient une routine d'une commande.

```bash
# Première fois seulement
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"

# À chaque utilisation : lancer, puis ouvrir http://127.0.0.1:8000
.venv\Scripts\python -m uvicorn app.web.main:app --reload
```

Ensuite, ouvre ton navigateur sur **http://127.0.0.1:8000**.

Pour ouvrir l'outil **depuis une autre machine du réseau** (ex. l'élève sur le même hotspot
téléphone), vois la section « Lancer l'API » du [README](../README.md) — c'est une option de
développement, à utiliser avec prudence car ce sont des données d'élèves.

---

## Ce que l'outil ne fait pas encore

Pour être transparent, voici ce qui reste à construire (l'outil est en **phase 1**) :

- **Pas d'écran pour l'élève** : pour l'instant, c'est toi qui saisis les réponses.
- **Le plan de progression n'est pas encore affiché** à l'écran (le moteur qui le calcule est prêt, l'affichage arrive).
- **Modules C (logique) et D (représentation)** : à venir.
- **Révisions espacées automatiques** : à venir (phase 3).

La prochaine étape concrète est de **tester sur 2 ou 3 vrais élèves** pour valider l'ensemble
(c'est le critère de passage de la phase 1).

---

## Pour aller plus loin

Quand tu seras à l'aise, voici où creuser :

- **[SPEC.md](../SPEC.md)** — la spécification complète (la « loi » du projet).
- **[README.md](../README.md)** — installer, lancer, lancer les tests.
- **[docs/01-reformulation.md](01-reformulation.md)** — le résumé et les décisions de départ.
- **[docs/04-spec-moteur.md](04-spec-moteur.md)** — comment le moteur décide (en pseudo-code).
- **[docs/ETAT.md](ETAT.md)** — où en est le projet, ce qui reste à faire.
- **[docs/07-roadmap-phase1.md](07-roadmap-phase1.md)** — la feuille de route de la phase 1.
