# Closed forms for two sums

**Abstract.** We give closed forms for the sum of the first n odd numbers and for the sum of the first n positive integers.

## 1. Definitions

**Definition 1.** For an integer n ≥ 0, O(n) is the sum 1 + 3 + … + (2n − 1) of the first n odd numbers, and S(n) is the sum 1 + 2 + … + n of the first n positive integers; O(0) = S(0) = 0.

## 2. Results

**Lemma 2.** For every integer n ≥ 0, O(n) = n².

*Proof.* By induction on n. O(0) = 0 = 0². If O(n) = n², then O(n + 1) = O(n) + (2n + 1) = n² + 2n + 1 = (n + 1)². ∎

**Proposition 3.** For every integer n ≥ 0, S(n) = n(n − 1)/2.

*Proof.* By induction on n. S(0) = 0. If S(n) = n(n − 1)/2, then S(n + 1) = S(n) + (n + 1) = n(n − 1)/2 + (n + 1), which is (n + 1)n/2. ∎

**Example 4.** O(3) = 1 + 3 + 5 = 9 = 3², and S(3) = 1 + 2 + 3 = 6.
