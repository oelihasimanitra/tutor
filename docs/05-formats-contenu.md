# Livrable 5 — Formats des fichiers de contenu

Le contenu est **versionné sous Git** (dossier `app/content/`) puis importé en base. Deux fichiers :
le graphe de compétences et les gabarits d'items. Les réponses sont **calculées par sympy**, jamais
produites par un LLM.

## 5.1 Format du graphe (`app/content/graph/num_alg.yaml`)

```yaml
version: 1
noeuds:
  - id: ALG.EQ1.01              # identifiant unique, stable
    domaine: ALG                # NUM PRO ALG GEO ESP FON STA LOG
    chapitre: "Équations du premier degré"
    intitule: "Résoudre x + a = b"
    niveau_ref: "5e"
    difficulte: 2               # 1..5
    type: procedure             # procedure | concept | modelisation | raisonnement
    prerequis: []               # ids des prérequis (arêtes DURES)
    liens_faibles: []           # ids des liens faibles
    erreurs_types: [procedure, concept]
    seuil_maitrise:             # OPTIONNEL : override du seuil global de config
      reussites: 3
      sur: 4
    items: [ALG.EQ1.01.i1, ALG.EQ1.01.i2]   # gabarits attachés
```

## 5.2 Format des gabarits (`app/content/items/*.yaml`)

```yaml
version: 1
gabarits:
  - id: ALG.EQ1.01.i1
    competence_id: ALG.EQ1.01
    type: equation_ax_plus_b    # nom de la fonction génératrice (voir engine/items.py)
    difficulte: 2
    format_reponse: entier      # entier | fraction | expression | qcm
    enonce: "Résous l'équation ${a}x + ${b} = ${c}."
    variables:                  # variables bornées, tirées au hasard (seedé)
      a: {type: int, min: 1, max: 9}
      b: {type: int, min: 1, max: 20}
      c: {type: int, min: 1, max: 50}
    reponse: "(${c} - ${b}) / ${a}"   # expression sympy, évaluée après substitution
    methode: "Isoler ${a}x, puis diviser par ${a}."   # traçage (cf. P2)
```

Règles : `enonce` est un template `string.Template` (`${var}`) ; `reponse` est une expression sympy ;
`variables` définit les bornes de chaque variable. Le moteur tire les valeurs (RNG seedé, donc
reproductible), substitue dans `enonce` et évalue `reponse`.

## 5.3 Cinq nœuds d'exemple

```yaml
version: 1
noeuds:
  - id: NUM.DIV.01
    domaine: NUM
    chapitre: "Nombres entiers"
    intitule: "Division euclidienne"
    niveau_ref: "5e"
    difficulte: 2
    type: procedure
    prerequis: []
    erreurs_types: [procedure, concept]
    items: [NUM.DIV.01.i1, NUM.DIV.01.i2]

  - id: NUM.FRA.02
    domaine: NUM
    chapitre: "Fractions"
    intitule: "Fractions équivalentes"
    niveau_ref: "5e"
    difficulte: 2
    type: concept
    prerequis: [NUM.DIV.01]      # la divisibilité fonde l'équivalence
    erreurs_types: [concept, procedure]
    items: [NUM.FRA.02.i1]

  - id: NUM.FRA.04
    domaine: NUM
    chapitre: "Fractions"
    intitule: "Addition de fractions (même dénominateur)"
    niveau_ref: "5e"
    difficulte: 2
    type: procedure
    prerequis: [NUM.FRA.02]
    erreurs_types: [procedure]
    items: [NUM.FRA.04.i1]

  - id: ALG.EQ1.01
    domaine: ALG
    chapitre: "Équations du premier degré"
    intitule: "Résoudre x + a = b"
    niveau_ref: "5e"
    difficulte: 2
    type: procedure
    prerequis: [NUM.FRA.04]      # manipuler une égalité de fractions/nombres
    erreurs_types: [procedure, concept]
    items: [ALG.EQ1.01.i1, ALG.EQ1.01.i2]

  - id: ALG.EQ1.03
    domaine: ALG
    chapitre: "Équations du premier degré"
    intitule: "Résoudre ax + b = c"
    niveau_ref: "4e"
    difficulte: 3
    type: procedure
    prerequis: [ALG.EQ1.01, ALG.EQ1.02]
    erreurs_types: [procedure, concept, lacune]
    items: [ALG.EQ1.03.i1]
```

## 5.4 Deux gabarits d'exemple

```yaml
version: 1
gabarits:
  - id: NUM.DIV.01.i1
    competence_id: NUM.DIV.01
    type: division_euclidienne_reste
    difficulte: 2
    format_reponse: entier
    enonce: "Quel est le reste de la division euclidienne de ${a} par ${b} ?"
    variables:
      a: {type: int, min: 20, max: 200}
      b: {type: int, min: 2, max: 9}
    reponse: "Mod(${a}, ${b})"
    methode: "Poser la division, quotient entier q, reste r = a - b*q."

  - id: ALG.EQ1.01.i1
    competence_id: ALG.EQ1.01
    type: equation_x_plus_a
    difficulte: 2
    format_reponse: entier
    enonce: "Résous l'équation x + ${a} = ${b}."
    variables:
      a: {type: int, min: -9, max: 9}
      b: {type: int, min: -20, max: 20}
    reponse: "${b} - ${a}"
    methode: "Soustraire ${a} des deux côtés."
```

> La fonction `Mod(a, b)` de sympy calcule le reste de la division euclidienne ; l'expression est
> évaluée côté moteur — aucune réponse n'est écrite à la main dans la base.
