# Guard F-1-4 — [false statement] Algorithm 7 and its Correctness paragraph — starting pass i at i skips needed comparisons — L = (2,3,1)
# Original statement: Algorithm 7 (pass i from position i to n) returns the same list as Algorithm 2, hence L sorted.
# Fixed statement:    Algorithm 7 (pass i from position 1 to n - i + 1) returns the same list as Algorithm 2, hence L sorted, with n(n-1)/2 comparisons against (n-1)^2.
# Model: Definition 1 and Algorithms 2 and 7 of the document, encoded without reference to the fix.
# Consequences covered: F-1-5 (abstract and conclusion).
import itertools


def pass_(L, a, b, count):
    L = list(L)
    for j in range(a, b):
        count[0] += 1
        if L[j - 1] > L[j]:
            L[j - 1], L[j] = L[j], L[j - 1]
    return L


def algorithm_2(L):
    L, n, c = list(L), len(L), [0]
    for i in range(1, n):
        L = pass_(L, 1, n, c)
    return L, c[0]


def algorithm_7_original(L):
    L, n, c = list(L), len(L), [0]
    for i in range(1, n):
        L = pass_(L, i, n, c)
    return L, c[0]


def algorithm_7_fixed(L):
    L, n, c = list(L), len(L), [0]
    for i in range(1, n):
        L = pass_(L, 1, n - i + 1, c)
    return L, c[0]


def original_statement(L):
    return algorithm_7_original(L)[0] == algorithm_2(L)[0] == sorted(L)


def fixed_statement(L):
    n = len(L)
    out, cmps = algorithm_7_fixed(L)
    return out == algorithm_2(L)[0] == sorted(L) and cmps == n * (n - 1) // 2 and algorithm_2(L)[1] == max(n - 1, 0) ** 2


WITNESS = (2, 3, 1)
VARIANTS = [(3, 2, 1), (1, 2, 0, 3), (2, 2, 1), (5, 4, 3, 2, 1)]
NEAR_CASE = (3, 1, 2)  # one full pass already sorts it: the original is right here too


def test_F_1_4_original_refuted_by_witness():
    assert not original_statement(WITNESS)


def test_F_1_4_fixed_holds_on_witness_and_variants():
    for c in [WITNESS, *VARIANTS]:
        assert fixed_statement(c), c


def test_F_1_4_near_case_where_original_is_true():
    assert original_statement(NEAR_CASE) and fixed_statement(NEAR_CASE)


def test_F_1_4_fixed_exhaustive_on_bounded_domain():
    for n in range(0, 7):
        for L in itertools.product(range(4), repeat=n):
            assert fixed_statement(L), L


def test_F_1_4_stability_of_fixed_algorithm_7():
    # Proposition 4 on tagged elements: equal keys keep their order
    for n in range(0, 6):
        for keys in itertools.product(range(3), repeat=n):
            tagged = [(k, t) for t, k in enumerate(keys)]
            L = list(tagged)
            for i in range(1, n):
                for j in range(1, n - i + 1):
                    if L[j - 1][0] > L[j][0]:
                        L[j - 1], L[j] = L[j], L[j - 1]
            assert L == sorted(tagged), keys
