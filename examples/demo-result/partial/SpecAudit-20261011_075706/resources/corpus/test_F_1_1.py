# Guard F-1-1 — [false statement] Lemma 3 — states the i SMALLEST are in place after i passes — L = (2, 3, 1), i = 1
# Original statement: "after the i-th pass of Algorithm 2, the i smallest elements of L occupy positions 1 to i, in increasing order."
# Fixed statement:    "... the i largest elements of L occupy positions n-i+1 to n, in increasing order." (statement fix)
# Model: Definition 1 (pass) and Algorithm 2 of the document, encoded without reference to the fix.
from itertools import permutations, product


def pass_(L, a, b=None):
    L = list(L)
    b = len(L) if b is None else b
    for j in range(a, b):  # 1-based j = a .. b-1 compares x_j, x_{j+1}
        if L[j - 1] > L[j]:
            L[j - 1], L[j] = L[j], L[j - 1]
    return L


def after_passes(L, i):
    for _ in range(i):
        L = pass_(L, 1)
    return L


def original_statement(L, i):
    n = len(L)
    return after_passes(L, i)[:i] == sorted(L)[:i]


def fixed_statement(L, i):
    n = len(L)
    return after_passes(L, i)[n - i:] == sorted(L)[n - i:]


WITNESS = ((2, 3, 1), 1)
VARIANTS = [((2, 3, 4, 1), 1), ((3, 1, 2), 2), ((2, 2, 1), 1)]
NEAR_CASE = ((1, 3, 2), 1)  # minimum already first: the original statement is true


def test_F_1_1_original_refuted_by_witness():
    assert not original_statement(*WITNESS)


def test_F_1_1_fixed_holds_on_witness_and_variants():
    for L, i in [WITNESS, *VARIANTS, NEAR_CASE]:
        assert fixed_statement(L, i), (L, i)


def test_F_1_1_near_case_where_original_is_true():
    assert original_statement(*NEAR_CASE) and fixed_statement(*NEAR_CASE)


def test_F_1_1_fixed_exhaustive_on_bounded_domain():
    for n in range(2, 7):
        for L in product(range(1, 4), repeat=n) if n <= 5 else permutations(range(1, n + 1)):
            for i in range(1, n):
                assert fixed_statement(L, i), (L, i)


def test_F_1_1_original_fails_on_some_permutation_of_each_size():
    for n in range(3, 6):
        assert any(not original_statement(L, 1) for L in permutations(range(1, n + 1)))
