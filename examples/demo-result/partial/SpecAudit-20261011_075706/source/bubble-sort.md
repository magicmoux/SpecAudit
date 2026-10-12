# Bubble sort and a faster variant

**Abstract.** We study the passes of bubble sort, derive a variant whose passes start further and further into the list, and show that both algorithms sort any list, stably.

## 1. Definitions

**Definition 1.** A *list* is a finite sequence L = (x_1, …, x_n) of integers, n = |L| being its length. A *pass* from position a to position b (1 ≤ a ≤ b ≤ n) compares x_j and x_{j+1} for j = a, a + 1, …, b − 1, in this order, and swaps them when x_j > x_{j+1}.

**Algorithm 2 (bubble sort).** Input: a list L of length n. Output: L in increasing order.

1. for i from 1 to n − 1: make a pass from position 1 to position n
2. return L

## 2. Results

**Lemma 3.** For every list L and every i with 1 ≤ i < |L|, after the i-th pass of Algorithm 2, the i smallest elements of L occupy positions 1 to i, in increasing order.

*Proof.* By induction on i. During a pass, whenever x_j > x_{j+1} the smaller element moves one position to the left, so the smallest element not yet in place moves left until it meets a smaller one, that is, until it reaches position i. ∎

**Proposition 4.** A pass, and hence any sequence of passes such as Algorithm 2, is stable: two equal elements of L keep their relative order.

*Proof.* A pass swaps two neighbours only when x_j > x_{j+1}, strictly, so two equal neighbours are never swapped. An element only moves by swapping with a neighbour, hence two equal elements never cross. ∎

**Corollary 5.** In Algorithm 2, the i-th pass can start at position i instead of position 1, without changing the output.

*Proof.* By Lemma 3, before the i-th pass positions 1 to i − 1 already hold their final elements, and none of them is greater than an element after it: the comparisons at these positions swap nothing. ∎

**Example 6.** For L = (3, 1, 2), the first pass compares 3 and 1 and swaps them, which gives (1, 3, 2).

## 3. A faster variant

**Algorithm 7 (bubble sort with a growing start).** Input: a list L of length n. Output: L in increasing order.

1. for i from 1 to n − 1: make a pass from position i to position n
2. return L

*Correctness.* By Corollary 8, Algorithm 7 returns the same list as Algorithm 2, hence L sorted. The i-th pass makes n − i comparisons, so Algorithm 7 makes n(n − 1)/2 comparisns in all, instead of (n − 1)² for Algorithm 2.

## 4. Conclusion

Algorithm 7, which starts each pass where the part of the list already sorted ends, sorts any list, stably, with about half the comparisons.
