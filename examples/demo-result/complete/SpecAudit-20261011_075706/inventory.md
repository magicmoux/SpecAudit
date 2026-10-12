# Inventory — bubble-sort.md

| Unit | Statement | Uses |
|---|---|---|
| Definition 1 | list of integers; pass from a to b compares x_j, x_{j+1} for j=a..b−1, swaps when x_j > x_{j+1} | — |
| Algorithm 2 | for i=1..n−1: pass 1→n; return L | Def 1 |
| Lemma 3 | after i-th pass of Alg 2, i smallest elements at positions 1..i, increasing | Def 1, Alg 2 |
| Proposition 4 | a pass, and any sequence of passes, is stable | Def 1 |
| Corollary 5 | in Alg 2, i-th pass can start at position i without changing output | Lemma 3 |
| Example 6 | L=(3,1,2): first pass gives (1,3,2) | Def 1, Alg 2 |
| Algorithm 7 | for i=1..n−1: pass i→n; return L | Def 1 |
| Correctness of Alg 7 | same output as Alg 2 (cites "Corollary 8"); n(n−1)/2 comparisons vs (n−1)² | Cor 5 (as cited), Alg 2, Alg 7 |
| Abstract | both algorithms sort any list, stably | Alg 2, Alg 7, Prop 4 |
| Conclusion | Alg 7 sorts any list, stably, with about half the comparisons | Alg 7, Prop 4, Correctness |
