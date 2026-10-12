# Guard F-1-5 — [wrong computed example] Example 6 — gives (1, 3, 2) as the result of the first pass — L = (3, 1, 2)
# Original statement: "the first pass compares 3 and 1 and swaps them, which gives (1, 3, 2)."
# Fixed statement:    the pass goes on, compares 3 and 2, swaps them, and returns (1, 2, 3). (statement fix)
# Model: Definition 1 (pass from position 1 to n) of the document, encoded without reference to the fix.
from itertools import permutations


def pass_(L, a, b):
    L = list(L)
    for j in range(a, b):
        if L[j - 1] > L[j]:
            L[j - 1], L[j] = L[j], L[j - 1]
    return L


def original_statement(L):
    return pass_(L, 1, len(L)) == [1, 3, 2]


def fixed_statement(L):
    return pass_(L, 1, len(L)) == [1, 2, 3]


WITNESS = (3, 1, 2)
VARIANTS = [(1, 2, 3), (2, 3, 1)]


def test_F_1_5_original_refuted_by_witness():
    assert not original_statement(WITNESS)


def test_F_1_5_fixed_holds_on_witness():
    assert fixed_statement(WITNESS)


def test_F_1_5_variants_and_near_case():
    assert pass_((2, 3, 1), 1, 3) == [2, 1, 3]
    assert pass_((1, 2, 3), 1, 3) == [1, 2, 3]
    assert pass_(WITNESS, 1, 2) == [1, 3, 2]  # near-case: the original is true for a pass stopped at position 2


def test_F_1_5_exhaustive_n3_last_element_is_max():
    for L in permutations(range(1, 4)):
        assert pass_(L, 1, 3)[-1] == 3
