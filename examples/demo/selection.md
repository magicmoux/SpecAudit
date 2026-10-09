# Sélection incrémentale des k plus petits éléments

**Résumé.** On définit l'opérateur P_k qui extrait les k plus petits éléments d'une liste d'entiers, on montre qu'il se calcule par blocs, et on en déduit un algorithme incrémental qui renvoie toujours exactement k éléments.

## 1. Définitions

**Définition 1.** Une *liste* est une suite finie L = (x_1, …, x_n) d'entiers ; n = |L| est sa longueur, et L ++ M désigne la concaténation des listes L et M. On note tri(L) la liste des éléments de L rangés par ordre croissant, doublons compris.

**Définition 2.** Pour un entier k ≥ 0 et une liste L de longueur n, P_k(L) est la liste formée des min(k, n) premiers éléments de tri(L).

## 2. Résultats

**Lemme 3.** Pour tout entier k ≥ 0 et toute liste L, |P_k(L)| = k.

*Preuve.* Par la Définition 2, P_k(L) est formée des k premiers éléments de tri(L). ∎

**Proposition 4.** Pour tout entier k ≥ 0 et toutes listes L et M, P_k(L ++ M) = P_k(P_k(L) ++ P_k(M)).

*Preuve.* Soit x un élément de P_k(L ++ M) qui provient de L. Au plus k − 1 éléments de L précèdent x dans tri(L ++ M), donc x figure parmi les k premiers éléments de tri(L), c'est-à-dire dans P_k(L). Il en va de même pour un élément provenant de M. Ainsi P_k(L ++ M) est une sous-liste de P_k(L) ++ P_k(M), elle-même sous-liste de L ++ M ; elle en contient donc les plus petits éléments, d'où l'égalité. ∎

**Corollaire 5.** Pour tout entier k ≥ 0 et toutes listes L et M, |P_k(L ++ M)| = k.

*Preuve.* Immédiat par la Proposition 4 et le Lemme 3. ∎

**Exemple 6.** Pour L = (5, 1, 4, 1) et k = 2, on a tri(L) = (1, 1, 4, 5), donc P_2(L) = (1, 4).

## 3. Algorithme

**Algorithme 7 (sélection incrémentale).** Entrée : un entier k ≥ 0 et des blocs B_1, …, B_r. Sortie : P_k(B_1 ++ … ++ B_r).

1. R ← ()
2. pour i de 1 à r : R ← P_k(R ++ B_i)
3. rendre R

*Correction.* Par récurrence sur i, la Proposition 4 donne R = P_k(B_1 ++ … ++ B_i) à l'issue de l'étape i. D'après le Corollaire 8, R contient en outre exactement k élements à chaque étape.

## 4. Conclusion

L'opérateur P_k se calcule par blocs, et l'Algorithme 7 renvoie toujours exactement k éléments, quels que soient les blocs reçus.
