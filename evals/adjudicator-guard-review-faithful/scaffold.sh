#!/usr/bin/env bash
# Lemma 3 already fixed in the document; the guard follows Definitions 1 and 2, duplicates included.
. "$(dirname "$0")/../_fixtures/demo-repo.sh"
sed -i 's/every list L, |P_k(L)| = k\./every list L, |P_k(L)| = min(k, |L|)./' selection.md
mkdir -p spec-guards
cat > spec-guards/test_F_1_1.py <<'PY'
import itertools

def P(k, L):
    return sorted(L)[: min(k, len(L))]

def test_original_refuted_by_witness():
    assert len(P(2, (3,))) != 2

def test_fixed_lemma_3_bounded():
    for n in range(4):
        for L in itertools.product(range(3), repeat=n):
            for k in range(5):
                assert len(P(k, L)) == min(k, len(L)), (k, L)
PY
