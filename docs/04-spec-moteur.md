# Livrable 4 — Spécification du moteur (pseudo-code)

Le moteur est un module Python pur. Il manipule des structures en mémoire (graphe, réponses, états) et
ne lit aucun seuil en dur : tout vient de la config. Les identifiants sont en anglais, la prose en
français.

## 1. Sélection du prochain item (adaptatif)

```
FONCTION prochain_item(eleve, etats, plan, graphe, config):
    noeud = noeud_courant(eleve, etats, plan)     # point d'entrée : niveau déclaré / noeuds_suspects

    POUR i DANS 1..PROFONDEUR_MAX:                # borne anti-boucle
        s = etats[noeud].statut
        SI s IN {acquis, consolide}:
            # MONTER : successeur direct non maîtrisé, sinon nœud suivant du plan
            suivants = [succ POUR succ DANS successeurs(noeud) SI non_maitrise(etats[succ])]
            SI suivants non vide: noeud = suivants[0]
            SINON: noeud = prochain_noeud_plan(plan)
        SINON SI s == fragile OU prerequis_non_maitrises(noeud) non vide:
            # DESCENDRE : tester un prérequis direct non maîtrisé (durs d'abord)
            pre = [p POUR p DANS prerequis(noeud) SI non_maitrise(etats[p])]
            SI pre non vide: noeud = pre[0]
        SINON:
            RETOURNER generer_item(noeud, eleve, config)   # on pose un item de ce nœud

    # Ajustement par l'affect (module A)
    SI anxiete(eleve) == elevee: choisir l'item de difficulte minimale, sans chronometre
    SI attention(eleve) == courte: signaler un bloc de 10-15 min
```

## 2. Mise à jour des statuts d'une compétence

```
FONCTION statut_noeud(noeud, reponses, config):
    tentatives = dernieres(reponses[noeud], config.seuils.maitrise.sur)   # fenêtre glissante
    reussites  = compter(t DANS tentatives SI t.est_correct
                         ET (non config.seuils.maitrise.methode_correcte OU t.methode_observee == methode_attendue))

    SI reussites >= config.seuils.maitrise.reussites:
        SI existe_controle_reussi(noeud, >= config.seuils.retention.delai_jours):
            RETOURNER (consolide, origine=controle)
        RETOURNER (acquis, origine=mesure, date_acquisition=aujourdhui)
    SINON SI tentatives non vide:
        RETOURNER (fragile, origine=mesure)
    SINON:
        RETOURNER (absent, origine=mesure)
```

## 3. Propagation des prérequis

Un nœud maîtrisé présume ses prérequis acquis. La propagation ne **crée pas** de mesure : elle pose un
statut inféré (`origine=propagation`) qui sera confirmé par un item de contrôle.

```
FONCTION propager(etats, graphe, config):
    POUR noeud DANS ordre_topologique(graphe):        # des prérequis vers les dépendants
        SI etats[noeud].statut IN {acquis, consolide} ET etats[noeud].origine == mesure:
            POUR pre DANS prerequis_durs(noeud):
                SI etats[pre].statut == absent:
                    etats[pre] = (acquis, origine=propagation)
```

Priorité de l'origine quand deux sources s'opposent : **mesure > controle > propagation**, et `M`
l'emporte toujours sur `D` (SPEC §3.8).

## 4. Planificateur (chemin critique + J+2 / J+7)

```
FONCTION construire_plan(cible_noeuds, etats, graphe, config):
    a_travailler = {}
    POUR cible DANS cible_noeuds:
        a_travailler |= prerequis_transitifs_non_maitrises(cible, etats, graphe)
        SI non_maitrise(etats[cible]): a_travailler |= {cible}

    ordre = ordre_topologique(a_travailler)          # prérequis avant dépendants

    echeances = {}
    POUR noeud DANS ordre:
        # révisions RELATIVES à la date d'acquisition (pas figées à l'avance)
        echeances[noeud] = {
            revision_j2: etats[noeud].date_acquisition + config.seuils.retention.revision_j2,
            revision_j7: etats[noeud].date_acquisition + config.seuils.retention.revision_j7,
        }
    RETOURNER Plan(noeuds_ordonnes=ordre, echeances=echeances)
```

## 5. Calcul des indicateurs (tous dérivés, recalculables)

```
FONCTION indicateurs(reponses, etats, plan, config):
    taux(domaine)    = reussites / tentatives   sur les réponses du domaine
    progression      = nb(etats IN {acquis, consolide}) / nb(noeuds du plan)
    calibration      = correlation(confiance_annoncee, est_correct)   # -1..1
    retention        = reussites_controle_j7 / tentatives_controle_j7
```

## 6. Règles de décision (module D + pilotage)

```
FONCTION decider_representation(blocs, config):
    POUR cycle DANS cycles:
        classer conditions par score T7_p (6 items)
        SI meilleure >= 2e + 2: gagnant[cycle] = meilleure
    SI gagnant[1] == gagnant[2]:  representation_efficace = gagnant (H renforcé)
    SINON SI un seul gagnant:      representation_efficace = gagnant (H faible)
    SINON:                         representation_efficace = 'M'   # rester multimodal
    # garde-fous : plaisir élevé + T7_p bas → motiver, pas installer ;
    # blocs à fidélité douteuse ou fatigue forte → exclus ou refaits.
```

Pilotage par l'affect (table de pilotage du SPEC, exprimée en config) : anxiété élevée → items faciles,
pas de chronomètre ; mindset bas → montrer des progrès chiffrés ; mauvaise calibration → exercices
« prédis ta réussite » ; attention courte → blocs de 10-15 min.

## 7. Cas limites

| Cas | Comportement |
| --- | --- |
| Cycle dans le graphe (arêtes dures) | **Rejet au chargement** (détection topologique) |
| Nœud sans item | Ignoré par la sélection, signalé dans un rapport de validation |
| Élève sans aucune réponse | Tous statuts `absent` ; plan = cibles + prérequis transitifs |
| Cible sans prérequis dans le périmètre | Plan = la cible seule |
| Item répété trop proche | Rotation des gabarits + seed différent (anti-répétition) |
| Réponse non parsable (saisie tuteur) | Marqué incorrect + `type_erreur`, jamais de crash |
| Moins de `sur` tentatives | Statut `fragile` tant que la fenêtre n'est pas pleine |
| Contrôle J+7 trop tôt (< 7 j) | Non compté comme consolidation |
| Propagation vs mesure en conflit | La **mesure** l'emporte toujours |
| Décision module D avec 1 seul cycle | `H` faible, pas de conclusion définitive |
