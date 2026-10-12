# Membership search in sorted blocks

**Abstract.** We recall binary search on a sorted list, and derive Algorithm 5, which decides whether a value occurs in any of several sorted blocks with a single binary search over their concatenation.

## 1. Definitions

**Definition 1.** A *list* is a finite sequence L = (x_1, …, x_n) of integers; n = |L| is its length, and A ++ B denotes the concatenation of the lists A and B. A list is *sorted* when x_1 ≤ x_2 ≤ … ≤ x_n. We write v ∈ L when v = x_i for some i.

**Algorithm 1 (binary search).** Input: a list L = (x_1, …, x_n) and an integer v. Output: true or false.

1. lo ← 1, hi ← n
2. while lo ≤ hi:
   1. mid ← ⌊(lo + hi) / 2⌋
   2. if x_mid = v, return true
   3. if x_mid < v, lo ← mid + 1; otherwise hi ← mid − 1
3. return false

We write bsearch(L, v) for its output.

## 2. Results

**Lemma 2.** For every sorted list L and every integer v, bsearch(L, v) = true if and only if v ∈ L.

*Proof.* The loop keeps the invariant: if v ∈ L, then v = x_i for some i with lo ≤ i ≤ hi. Initially it holds, since lo = 1 and hi = n. If x_mid < v, every x_i with i ≤ mid is at most x_mid < v, since L is sorted, so v is not among them and lo ← mid + 1 keeps the invariant; the case x_mid > v is symmetric. Each iteration decreases hi − lo, so the loop ends; it returns true only on some x_mid = v, and returns false only when lo > hi, where the invariant shows v ∉ L. ∎

**Proposition 3.** For all sorted lists A and B and every integer v, bsearch(A ++ B, v) = true if and only if v ∈ A or v ∈ B.

*Proof.* v ∈ A ++ B if and only if v ∈ A or v ∈ B, and Lemma 2 applied to A ++ B gives bsearch(A ++ B, v) = true if and only if v ∈ A ++ B. ∎

**Proposition 4.** For all sorted lists A and B such that every element of A is at most every element of B, and every integer v, bsearch(A ++ B, v) = true if and only if v ∈ A or v ∈ B.

*Proof.* A ++ B is sorted, since A and B are and every element of A is at most every element of B. Lemma 2 applied to A ++ B concludes, as in Proposition 3. ∎

**Algorithm 5 (search in blocks).** Input: sorted lists B_1, …, B_r with r ≥ 1, and an integer v. Output: true or false.

1. C ← B_1
2. for i from 2 to r: C ← C ++ B_i
3. return bsearch(C, v)

**Theorem 6.** For all sorted lists B_1, …, B_r with r ≥ 1 and every integer v, Algorithm 5 returns true if and only if v occurs in one of the blocks.

*Proof.* By induction on r, applying Proposition 3 to C and B_i at each step. ∎

**Example 7.** For the blocks (1, 4) and (6, 9), which satisfy the hypothesis of Proposition 4, and v = 6, binary search on (1, 4, 6, 9) checks x_2 = 4 < 6, then x_3 = 6, and returns true.

**Corollary 8.** For every sorted list L = (x_1, …, x_n) with n ≥ 2, every k with 1 ≤ k < n and every integer v, bsearch(L, v) = true if and only if v ∈ (x_1, …, x_k) or v ∈ (x_{k+1}, …, x_n).

*Proof.* Proposition 4 with A = (x_1, …, x_k) and B = (x_{k+1}, …, x_n), whose concatenation is L. ∎

## 3. Conclusion

A single binary search over the concatenation of sorted blocks decides membership in any of them (Theorem 6), so Algorithm 5 needs neither a merge nor one search per block.
