# Incremental selection of the k smallest elements

**Abstract.** We define the operator P_k that extracts the k smallest elements of a list of integers, show that it can be computed block by block, and derive an incremental algorithm that always returns exactly k elements.

## 1. Definitions

**Definition 1.** A *list* is a finite sequence L = (x_1, …, x_n) of integers; n = |L| is its length, and L ++ M denotes the concatenation of the lists L and M. We write sort(L) for the list of the elements of L in increasing order, duplicates included.

**Definition 2.** For an integer k ≥ 0 and a list L of length n, P_k(L) is the list formed by the first min(k, n) elements of sort(L).

## 2. Results

**Lemma 3.** For every integer k ≥ 0 and every list L, |P_k(L)| = k.

*Proof.* By Definition 2, P_k(L) is formed by the first k elements of sort(L). ∎

**Proposition 4.** For every integer k ≥ 0 and all lists L and M, P_k(L ++ M) = P_k(P_k(L) ++ P_k(M)).

*Proof.* Let x be an element of P_k(L ++ M) that comes from L. At most k − 1 elements of L precede x in sort(L ++ M), so x is among the first k elements of sort(L), that is, in P_k(L). The same holds for an element that comes from M. Thus P_k(L ++ M) is a sublist of P_k(L) ++ P_k(M), itself a sublist of L ++ M; it therefore contains its smallest elements, hence the equality. ∎

**Corollary 5.** For every integer k ≥ 0 and all lists L and M, |P_k(L ++ M)| = k.

*Proof.* Immediate from Proposition 4 and Lemma 3. ∎

**Example 6.** For L = (5, 1, 4, 1) and k = 2, we have sort(L) = (1, 1, 4, 5), hence P_2(L) = (1, 4).

## 3. Algorithm

**Algorithm 7 (incremental selection).** Input: an integer k ≥ 0 and blocks B_1, …, B_r. Output: P_k(B_1 ++ … ++ B_r).

1. R ← ()
2. for i from 1 to r: R ← P_k(R ++ B_i)
3. return R

*Correctness.* By induction on i, Proposition 4 gives R = P_k(B_1 ++ … ++ B_i) at the end of step i. By Corollary 8, R moreover contains exactly k elemnts at every step.

## 4. Conclusion

The operator P_k can be computed block by block, and Algorithm 7 always returns exactly k elements, whatever blocks it receives.
