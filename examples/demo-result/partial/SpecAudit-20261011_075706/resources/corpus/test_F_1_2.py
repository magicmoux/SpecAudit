# Guard F-1-2 — [false statement] Corollary 5 — pass i can start at position i — L = (2, 3, 1)
# Original statement: "the i-th pass can start at position i instead of position 1, without changing the output."
# Fixed statement:    "the i-th pass can stop at position n − i + 1 instead of position n, without changing the output." (statement fix)
# Model: Definition 1 (pass) and Algorithm 2 of the document, encoded without reference to the fix.
from itertools import permutations, product


def pass_(L, a, b):
    L = list(L)
    for j in range(a, b):  # 1-based j = a .. b-1 compares x_j, x_{j+1}
        if L[j - 1] > L[j]:
            L[j - 1], L[j] = L[j], L[j - 1]
    return L


def algorithm_2(L):
    n = len(L)
    for _ in range(1, n):
        L = pass_(L, 1, n)
    return L


def with_variable_passes(L, bounds):
    n = len(L)
    for i in range(1, n):
        a, b = bounds(i, n)
        L = pass_(L, a, b)
    return L


def original_statement(L):
    return with_variable_passes(L, lambda i, n: (i, n)) == algorithm_2(L)


def fixed_statement(L):
    return with_variable_passes(L, lambda i, n: (1, n - i + 1)) == algorithm_2(L)


WITNESS = (2, 3, 1)
VARIANTS = [(2, 1, 0), (1, 2, 0, 3), (2, 2, 1)]
NEAR_CASE = (3, 1, 2)  # both variants agree


def test_F_1_2_original_refuted_by_witness():
    assert not original_statement(WITNESS)


def test_F_1_2_fixed_holds_on_witness_and_variants():
    for L in [WITNESS, *VARIANTS, NEAR_CASE]:
        assert fixed_statement(L), L


def test_F_1_2_near_case_where_original_is_true():
    assert original_statement(NEAR_CASE) and fixed_statement(NEAR_CASE)


def test_F_1_2_fixed_exhaustive_on_bounded_domain():
    for n in range(2, 7):
        for L in product(range(1, 4), repeat=n) if n <= 5 else permutations(range(1, n + 1)):
            assert fixed_statement(L), L


def test_F_1_2_original_fails_on_some_permutation_of_each_size():
    for n in range(3, 6):
        assert any(not original_statement(L) for L in permutations(range(1, n + 1)))
