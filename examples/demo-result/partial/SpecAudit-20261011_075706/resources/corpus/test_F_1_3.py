# Guard F-1-3 — [algorithm] Algorithm 7 — passes from position i to n do not sort — L = (3, 2, 1) returns (2, 1, 3)
# Original statement: "Algorithm 7 (pass i from position i to n) returns L in increasing order."
# Proposed fix (critical fix, PENDING the user's approval, not applied to the document):
#   pass i from position 1 to n − i + 1 (Corollary 5).
# This file therefore has no text guard yet: there is no fixed text to assert.
# Model: Definition 1 (pass) of the document, encoded without reference to the fix.
from itertools import permutations, product


def pass_(L, a, b):
    L = list(L)
    for j in range(a, b):
        if L[j - 1] > L[j]:
            L[j - 1], L[j] = L[j], L[j - 1]
    return L


def run(L, bounds):
    n = len(L)
    for i in range(1, n):
        L = pass_(L, *bounds(i, n))
    return L


def original_statement(L):  # Algorithm 7 as written
    return run(L, lambda i, n: (i, n)) == sorted(L)


def proposed_statement(L):  # shrinking end, Corollary 5
    return run(L, lambda i, n: (1, n - i + 1)) == sorted(L)


WITNESS = (3, 2, 1)
VARIANTS = [(2, 3, 1), (2, 3, 4, 1), (2, 2, 1)]
NEAR_CASE = (2, 1)  # n = 2: a single full pass, Algorithm 7 sorts


def test_F_1_3_original_refuted_by_witness():
    assert run(WITNESS, lambda i, n: (i, n)) == [2, 1, 3]
    assert not original_statement(WITNESS)


def test_F_1_3_original_refuted_on_variants():
    assert all(not original_statement(L) for L in VARIANTS)


def test_F_1_3_near_case_where_original_is_true():
    assert original_statement(NEAR_CASE) and proposed_statement(NEAR_CASE)


def test_F_1_3_proposed_fix_exhaustive_on_bounded_domain():
    for n in range(2, 7):
        for L in product(range(1, 4), repeat=n) if n <= 5 else permutations(range(1, n + 1)):
            assert proposed_statement(L), L


def test_F_1_3_comparison_count_of_proposed_fix():
    for n in range(2, 9):
        assert sum(n - i for i in range(1, n)) == n * (n - 1) // 2
