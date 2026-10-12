# Bubble sort and a faster variant

**Abstract.** We study the passes of bubble sort, derive a variant whose passes end earlier and earlier in the list, and show that both algorithms sort any list, stably.

## 1. Definitions

**Definition 1.** A *list* is a finite sequence L = (x_1, …, x_n) of integers, n = |L| being its length. A *pass* from position a to position b (1 ≤ a ≤ b ≤ n) compares x_j and x_{j+1} for j = a, a + 1, …, b − 1, in this order, and swaps them when x_j > x_{j+1}. Below, "increasing" is meant in the weak sense (equal elements allowed), and the *elements* of a list are its entries, followed by position as they are swapped, so that two equal entries remain two distinct elements.

**Algorithm 2 (bubble sort).** Input: a list L of length n. Output: L in increasing order.

1. for i from 1 to n − 1: make a pass from position 1 to position n
2. return L

## 2. Results

**Lemma 3.** For every list L and every i with 1 ≤ i < |L|, after the i-th pass of Algorithm 2, the i largest elements of L occupy positions n − i + 1 to n, in increasing order, where n = |L|.

*Proof.* In a pass from position 1 to position n, after the comparison of positions j and j + 1, position j + 1 holds a largest element among those that stood at positions 1 to j + 1 when the pass began: this is clear for j = 1, and the comparison of positions j and j + 1 leaves the larger of the two at position j + 1. In particular a pass puts a largest element of the list at position n, which proves the case i = 1. Let i ≥ 2 and assume the statement for i − 1, so that positions n − i + 2 to n hold the i − 1 largest elements in increasing order before the i-th pass. When the comparison of positions n − i + 1 and n − i + 2 is made, position n − i + 1 holds a largest element of positions 1 to n − i + 1, that is, the i-th largest element of L, which is not greater than the element at position n − i + 2: nothing is swapped, and nor in the later comparisons, which are between elements already in increasing order. So after the i-th pass positions n − i + 1 to n hold the i largest elements in increasing order. For i = n − 1 (n ≥ 2), position 1 then holds the remaining element, which is not greater than the others, so Algorithm 2 sorts L; if n ≤ 1 there is no pass and L is already sorted. ∎

**Proposition 4.** A pass, and hence any sequence of passes such as Algorithm 2, is stable: two equal elements of L keep their relative order.

*Proof.* A pass swaps two neighbours only when x_j > x_{j+1}, strictly, so two equal neighbours are never swapped. An element only moves by swapping with a neighbour, hence two equal elements never cross. ∎

**Corollary 5.** In Algorithm 2, the i-th pass can end at position n − i + 1 instead of position n, without changing the output.

*Proof.* The two passes differ only by the comparisons of positions j and j + 1 for j = n − i + 1, …, n − 1 (none if i = 1). By Lemma 3, before the i-th pass positions n − i + 2 to n hold their final elements, in increasing order, and the proof of Lemma 3 shows that the comparison at j = n − i + 1 swaps nothing; the following ones are between elements already in increasing order and swap nothing either. Each pass therefore gives the same list, and so does the whole algorithm. ∎

**Example 6.** For L = (3, 1, 2), the first pass compares 3 and 1 and swaps them, which gives (1, 3, 2), then compares 3 and 2 and swaps them, which gives (1, 2, 3).

## 3. A faster variant

**Algorithm 7 (bubble sort with a shrinking end).** Input: a list L of length n. Output: L in increasing order.

1. for i from 1 to n − 1: make a pass from position 1 to position n − i + 1
2. return L

*Correctness.* By Corollary 5, Algorithm 7 returns the same list as Algorithm 2, hence L sorted. The i-th pass makes n − i comparisons, so Algorithm 7 makes n(n − 1)/2 comparisons in all, instead of (n − 1)² for Algorithm 2.

## 4. Conclusion

Algorithm 7, which ends each pass where the part of the list already sorted begins, sorts any list, stably, with about half the comparisons.
