# Inventory — bubble-sort.md

| Unit | Statement | Uses |
|---|---|---|
| Definition 1 | list, pass from a to b (compares x_j,x_{j+1}, j=a..b-1, swaps if x_j > x_{j+1}) | — |
| Algorithm 2 | for i=1..n-1: pass 1..n | Def 1 |
| Lemma 3 | after i-th pass of Alg 2, i smallest at positions 1..i, increasing | Def 1, Alg 2 |
| Proposition 4 | a pass / any sequence of passes is stable | Def 1 |
| Corollary 5 | i-th pass can start at i without changing output | Lemma 3, Alg 2 |
| Example 6 | L=(3,1,2): first pass gives (1,3,2) | Def 1 |
| Algorithm 7 | for i=1..n-1: pass i..n | Def 1 |
| Alg 7 correctness | cites "Corollary 8"; i-th pass n-i comparisons; total n(n-1)/2 vs (n-1)^2 | Cor 5 (as cited), Alg 2, Alg 7 |
| Abstract / Conclusion | both algorithms sort any list, stably; about half the comparisons | Lemma 3, Prop 4, Alg 7 correctness |
