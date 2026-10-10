#!/usr/bin/env bash
# The demo as a previous audit left it: Lemma 3 already fixed, and its guard in the corpus, committed. The guard is
# faulty: its model of P_k drops duplicates (set), against Definition 1, so the corpus is red at the baseline although
# the document is right on that point.
. "$(dirname "$0")/../_fixtures/demo-repo.sh"
sed -i 's/every list L, |P_k(L)| = k\./every list L, |P_k(L)| = min(k, |L|)./' selection.md
sed -i 's/P_k(L) is formed by the first k elements of sort(L)\./P_k(L) is formed by the first min(k, |L|) elements of sort(L)./' selection.md
mkdir -p spec-guards
cat > spec-guards/test_F_1_1.py <<'PY'
# Guard F-1-1 — [false statement] Lemma 3 — ignores min(k, n) of Definition 2 — L = (3), k = 2
import itertools

def P(k, L):
    return sorted(set(L))[: min(k, len(L))]

def test_F_1_1_original_refuted_by_witness():
    assert len(P(2, (3,))) != 2

def test_F_1_1_fixed_exhaustive_bounded():
    for n in range(4):
        for L in itertools.product(range(3), repeat=n):
            for k in range(5):
                assert len(P(k, L)) == min(k, len(L)), (k, L)
PY
git -c user.name=eval -c user.email=eval@example.invalid add selection.md spec-guards
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Previous audit: Lemma 3 fixed, guard F-1-1"
