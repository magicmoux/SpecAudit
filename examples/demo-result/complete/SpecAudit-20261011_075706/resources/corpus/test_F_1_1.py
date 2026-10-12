# Guard F-1-1 — [false statement] Lemma 3 — a left-to-right pass carries the largest elements to the end, not the smallest to the front — L = (2,3,1)
# Original statement: after the i-th pass of Algorithm 2, the i smallest elements occupy positions 1..i, in increasing order.
# Fixed statement:    after the i-th pass of Algorithm 2, the i largest elements occupy positions n-i+1..n, in increasing order.
# Model: Definition 1 and Algorithm 2 of the document (pass from a to b swaps x_j, x_{j+1} when x_j > x_{j+1}), encoded without reference to the fix.
# Consequences covered: F-1-3 (Corollary 5: starting pass i at position i), F-1-4 (Algorithm 7), same witness.
import itertools


def pass_(L, a, b):
    """Definition 1, 1-indexed a <= b."""
    L = list(L)
    for j in range(a, b):
        if L[j - 1] > L[j]:
            L[j - 1], L[j] = L[j], L[j - 1]
    return L


def after_passes(L, i):
    n = len(L)
    for _ in range(i):
        L = pass_(L, 1, n)
    return L


def original_statement(L, i):
    M = after_passes(L, i)
    return M[:i] == sorted(L)[:i]


def fixed_statement(L, i):
    n = len(L)
    M = after_passes(L, i)
    return M[n - i:] == sorted(L)[n - i:]


def algorithm_7(L):
    n = len(L)
    for i in range(1, n):
        L = pass_(L, i, n)
    return L


WITNESS = ((2, 3, 1), 1)
VARIANTS = [((1, 2, 0, 3), 1), ((2, 2, 1), 1), ((5, 4, 3, 2, 1), 2)]
NEAR_CASE = ((3, 1, 2), 1)  # smallest element happens to end in front: original true as well


def test_F_1_1_original_refuted_by_witness():
    assert not original_statement(*WITNESS)


def test_F_1_1_original_refuted_on_variants():
    assert not all(original_statement(*c) for c in VARIANTS)


def test_F_1_1_fixed_holds_on_witness_and_variants():
    for c in [WITNESS, *VARIANTS]:
        assert fixed_statement(*c), c


def test_F_1_1_near_case_where_original_is_true():
    assert original_statement(*NEAR_CASE) and fixed_statement(*NEAR_CASE)


def test_F_1_1_fixed_exhaustive_on_bounded_domain():
    for n in range(2, 6):
        for L in itertools.product(range(4), repeat=n):
            for i in range(1, n):
                assert fixed_statement(L, i), (L, i)


def test_F_1_3_consequence_algorithm_7_fails_on_cause_witness():
    # the original Corollary 5 would make Algorithm 7 equal to Algorithm 2 on the witness
    assert algorithm_7((2, 3, 1)) != sorted((2, 3, 1))
