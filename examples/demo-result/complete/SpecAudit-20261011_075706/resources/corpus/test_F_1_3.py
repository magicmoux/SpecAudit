# Guard F-1-3 — [false statement] Corollary 5 — positions 1..i-1 are not final after i-1 passes, so pass i cannot start at i — L = (3,2,1)
# Original statement: in Algorithm 2 the i-th pass can start at position i instead of 1 without changing the output.
# Fixed statement:    in Algorithm 2 the i-th pass can end at position n-i+1 instead of n, each pass giving the same list.
# Model: Definition 1 and Algorithm 2 of the document, encoded without reference to the fix.
# Consequences covered: F-1-4 (Algorithm 7 must use the fixed passes), same witness.
import itertools


def pass_(L, a, b):
    L = list(L)
    for j in range(a, b):
        if L[j - 1] > L[j]:
            L[j - 1], L[j] = L[j], L[j - 1]
    return L


def algorithm_2(L):
    n = len(L)
    for i in range(1, n):
        L = pass_(L, 1, n)
    return L


def start_at_i(L):
    n = len(L)
    for i in range(1, n):
        L = pass_(L, i, n)
    return L


def end_at_n_minus_i_plus_1(L):
    n = len(L)
    for i in range(1, n):
        L = pass_(L, 1, n - i + 1)
    return L


def original_statement(L):
    return start_at_i(L) == algorithm_2(L)


def fixed_statement(L):
    return end_at_n_minus_i_plus_1(L) == algorithm_2(L)


WITNESS = (3, 2, 1)
VARIANTS = [(2, 3, 1), (1, 2, 0, 3), (4, 3, 2, 1)]
NEAR_CASE = (3, 1, 2)  # the original statement is true here as well


def test_F_1_3_original_refuted_by_witness():
    assert not original_statement(WITNESS)


def test_F_1_3_fixed_holds_on_witness_and_variants():
    for c in [WITNESS, *VARIANTS]:
        assert fixed_statement(c), c


def test_F_1_3_near_case_where_original_is_true():
    assert original_statement(NEAR_CASE) and fixed_statement(NEAR_CASE)


def test_F_1_3_fixed_exhaustive_on_bounded_domain():
    for n in range(0, 7):
        for L in itertools.product(range(4), repeat=n):
            assert fixed_statement(L), L
