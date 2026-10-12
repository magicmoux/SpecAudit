# Guard F-2-1 — [incomplete proof] sortedness of Algorithm 2 — the last step of Lemma 3 (i = n-1, then position 1) is never written — no counterexample, the claim is true
# Intermediate claim of the faulty step: after the n-1 passes of Algorithm 2 (n >= 2), positions 2..n hold the n-1 largest elements in increasing order
# and position 1 holds the remaining element, no greater than position 2; hence the list is sorted. For n <= 1 there is no pass and the list is sorted.
# Model: Definition 1 and Algorithm 2 of the document.
import itertools


def pass_(L, a, b):
    L = list(L)
    for j in range(a, b):
        if L[j - 1] > L[j]:
            L[j - 1], L[j] = L[j], L[j - 1]
    return L


def algorithm_2(L):
    L, n = list(L), len(L)
    for i in range(1, n):
        L = pass_(L, 1, n)
    return L


def intermediate_claim(L):
    n = len(L)
    M = algorithm_2(L)
    if n <= 1:
        return M == list(L)
    return M[1:] == sorted(L)[1:] and M[0] <= M[1] and M[0] == sorted(L)[0] and M == sorted(L)


def test_F_2_1_witness_and_variants():
    for c in [(2, 3, 1), (3, 2, 1), (2, 2, 1), (1, 1), (5,), ()]:
        assert intermediate_claim(c), c


def test_F_2_1_near_case_one_pass_suffices():
    assert intermediate_claim((3, 1, 2))


def test_F_2_1_bounded_exhaustive():
    for n in range(0, 8):
        for L in itertools.product(range(4), repeat=n):
            assert intermediate_claim(L), L
