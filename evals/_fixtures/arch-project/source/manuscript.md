# Incremental selection of the k smallest elements

**Abstract.** We define the operator P_k that extracts the k smallest elements of a list of integers, and show that it can be computed block by block.

## 1. Definitions

**Definition 1.** A *list* is a finite sequence L = (x_1, …, x_n) of integers; n = |L| is its length, and L ++ M is the concatenation of L and M. sort(L) is the list of the elements of L in increasing order, duplicates included.

**Definition 2.** For an integer k ≥ 0 and a list L, P_k(L) is the list formed by the first k elements of sort(L).

## 2. Results

**Lemma 3.** For every integer k ≥ 0 and every list L, |P_k(L)| = k.

*Proof.* By Definition 2. ∎

**Proposition 4.** For every integer k ≥ 0 and all lists L and M, P_k(L ++ M) = P_k(P_k(L) ++ P_k(M)).

*Proof.* An element of P_k(L ++ M) that comes from L has at most k − 1 elements of L before it in sort(L ++ M), so it is in P_k(L); likewise for M. ∎

## References

[FR75] R. W. Floyd and R. L. Rivest. Expected time bounds for selection. Communications of the ACM 18(3), 1975.
