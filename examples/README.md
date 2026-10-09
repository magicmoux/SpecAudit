# Exemple : sélection incrémentale

[`demo/selection.md`](demo/selection.md) est une courte spécification, une page à peine, qui contient volontairement des erreurs : une cause, la chaîne de conséquences qu'elle entraîne, une erreur indépendante et deux défauts de forme. Elle permet de voir un audit complet en quelques minutes, sans risque pour vos propres documents.

## Essayer

L'audit a besoin d'un dépôt git et crée son worktree à côté de lui. Préparez un dépôt jetable :

```bash
mkdir spec-audit-demo
cd spec-audit-demo
git init
curl -O https://raw.githubusercontent.com/magicmoux/SpecAudit/main/examples/demo/selection.md
git add selection.md
git commit -m "Spécification de démonstration"
claude
```

(Depuis un clone du dépôt, remplacez `curl` par une copie de `examples/demo/selection.md`.)

Puis, dans Claude Code :

```text
/spec-audit:spec-audit selection.md --max-iter 2
```

Le worktree est créé dans `../spec-audit-demo-audit-selection`, sur la branche `audit/selection`. Les gardes, en Python, sont écrites dans `spec-guards/`.

## Ce que l'audit doit trouver

Lisez cette section après l'audit, pour comparer avec son rapport.

<details>
<summary>Erreurs et défauts introduits</summary>

| Passage | Nature | Témoin | Place dans le graphe |
|---|---|---|---|
| Lemme 3 : \|P_k(L)\| = k | énoncé faux : ignore le cas k > n | k = 3, L = (1, 2) : \|P_3(L)\| = 2 | racine |
| Corollaire 5 : \|P_k(L ++ M)\| = k | énoncé faux, hérité du Lemme 3 | k = 3, L = (1), M = (2) | conséquence du Lemme 3 |
| Correction de l'Algorithme 7 : « exactement k éléments » | affirmation fausse, héritée du Corollaire 5 | k = 3, blocs (2) puis (1) : R = (1, 2) | conséquence du Corollaire 5 |
| Résumé et Conclusion | affirment plus que le corps ne démontre | idem | conséquences de la même chaîne |
| Exemple 6 : P_2(L) = (1, 4) | exemple calculé faux : doublons | L = (5, 1, 4, 1) : P_2(L) = (1, 1) | racine indépendante |
| Correction de l'Algorithme 7 : « Corollaire 8 » | défaut de forme : renvoi vers un résultat inexistant (Corollaire 5) | — | voie éditoriale |
| Correction de l'Algorithme 7 : « élements » | défaut de forme : typo | — | voie éditoriale |

La Proposition 4 et la sortie de l'Algorithme 7 sont justes : une correction qui les modifierait serait une sur-correction. La correction minimale attendue du Lemme 3 est |P_k(L)| = min(k, |L|), ou l'ajout de l'hypothèse k ≤ |L|, après quoi les conséquences se corrigent à leur tour.

Les relecteurs peuvent aussi relever des lacunes de preuve réelles mais non introduites à dessein : le traitement des doublons dans la preuve de la Proposition 4, ou l'idempotence P_k(P_k(L)) = P_k(L), utilisée sans être énoncée dans la correction de l'Algorithme 7.

</details>
