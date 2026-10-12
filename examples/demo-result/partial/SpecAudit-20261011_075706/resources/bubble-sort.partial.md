# Bubble sort and a faster variant

**Abstract.** We study the passes of bubble sort, derive a variant whose passes start further and further into the list, and show that both algorithms sort any list, stably.

## 1. Definitions

**Definition 1.** A *list* is a finite sequence L = (x_1, …, x_n) of integers, n = |L| being its length. A *pass* from position a to position b (1 ≤ a ≤ b ≤ n) compares x_j and x_{j+1} for j = a, a + 1, …, b − 1, in this order, and swaps them when x_j > x_{j+1}.

**Algorithm 2 (bubble sort).** Input: a list L of length n. Output: L in increasing order.

1. for i from 1 to n − 1: make a pass from position 1 to position n
2. return L

## 2. Results

**Lemma 3.** For every list L and every i with 1 ≤ i < |L|, after the i-th pass of Algorithm 2, the i largest elements of L occupy positions n − i + 1 to n, in increasing order, where n = |L|.

*Proof.* By induction on i. During a pass from position 1 to position n, the element at position j after the comparison of x_j and x_{j+1} is the larger of the two, so the largest element met so far is carried to the right until it meets an element at least as large, or reaches position n. Hence a pass leaves a largest element of the list at position n, which is the case i = 1. For the step, the i-th pass does not move the elements at positions n − i + 2 to n, already the i − 1 largest in increasing order, past one another or past a smaller element (each of them is at least as large as everything before it, so no swap involves it as the smaller element of a pair); on the first n − i + 1 positions it acts as a pass, which leaves a largest remaining element at position n − i + 1. ∎

**Proposition 4.** A pass, and hence any sequence of passes such as Algorithm 2, is stable: two equal elements of L keep their relative order.

*Proof.* A pass swaps two neighbours only when x_j > x_{j+1}, strictly, so two equal neighbours are never swapped. An element only moves by swapping with a neighbour, hence two equal elements never cross. ∎

**Corollary 5.** In Algorithm 2, the i-th pass can stop at position n − i + 1 instead of position n, without changing the output.

*Proof.* For i = 1 there is nothing to prove. For i ≥ 2, by Lemma 3, before the i-th pass positions n − i + 2 to n hold the i − 1 largest elements of L, in increasing order, so none of them is smaller than an element before it: the comparisons at j = n − i + 1, …, n − 1 swap nothing, whatever the pass has done to positions 1 to n − i + 1. ∎

**Example 6.** For L = (3, 1, 2), the first pass compares 3 and 1 and swaps them, which gives (1, 3, 2); it then compares 3 and 2 and swaps them, so the pass returns (1, 2, 3).

## 3. A faster variant

**Algorithm 7 (bubble sort with a growing start).** Input: a list L of length n. Output: L in increasing order.

1. for i from 1 to n − 1: make a pass from position i to position n
2. return L

*Correctness.* By Corollary 8, Algorithm 7 returns the same list as Algorithm 2, hence L sorted. The i-th pass makes n − i comparisons, so Algorithm 7 makes n(n − 1)/2 comparisons in all, instead of (n − 1)² for Algorithm 2.

## 4. Conclusion

Algorithm 7, which starts each pass where the part of the list already sorted ends, sorts any list, stably, with about half the comparisons.
