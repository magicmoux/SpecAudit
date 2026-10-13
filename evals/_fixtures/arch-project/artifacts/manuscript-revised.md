# Incremental selection of the k smallest elements

**Abstract.** We define the operator P_k that extracts the k smallest elements of a list of integers, show that it can be computed block by block, and derive an incremental algorithm.

## 1. Definitions

**Definition 1.** A *list* is a finite sequence L = (x_1, …, x_n) of integers; n = |L| is its length, and L ++ M is the concatenation of L and M. sort(L) is the list of the elements of L in increasing order, duplicates included.

**Definition 2.** For an integer k ≥ 0 and a list L of length n, P_k(L) is the list formed by the first min(k, n) elements of sort(L).

## 2. Results

**Lemma 3.** For every integer k ≥ 0 and every list L, |P_k(L)| = k.

*Proof.* See `proofs/lemma-3.md`. ∎

**Proposition 4.** For every integer k ≥ 0 and all lists L and M, P_k(L ++ M) = P_k(P_k(L) ++ P_k(M)).

*Proof.* See `proofs/proposition-4.md`. ∎

## 3. Algorithm

**Algorithm 5 (incremental selection).** Input: k ≥ 0 and blocks B_1, …, B_r. Output: P_k(B_1 ++ … ++ B_r).
R ← (); for i from 1 to r: R ← P_k(R ++ B_i); return R. Correct by induction on i and Proposition 4.

## 4. Mechanization

Definition 2, Lemma 3 and Proposition 4 are mechanized in Lean; `mechanization/CORRESPONDENCE.md` gives the names.

## References

[FR75] R. W. Floyd and R. L. Rivest. Expected time bounds for selection. Communications of the ACM 18(3):165–172, 1975.
