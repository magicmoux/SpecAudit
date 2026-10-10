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
# The corpus carries its own runner: the eval sandbox has no pytest, and an oracle whose command does not run is not an
# oracle, so the audit would stop at phase 0.
cat > spec-guards/run_guards.py <<'PY'
"""Runs every test_* function of the test_*.py files beside this script; exit 1 if any fails."""
import importlib.util, pathlib, sys, traceback

failed = 0
for path in sorted(pathlib.Path(__file__).parent.glob("test_*.py")):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        try:
            getattr(module, name)()
            print(f"PASS {path.name}::{name}")
        except Exception:
            failed += 1
            print(f"FAIL {path.name}::{name}")
            traceback.print_exc(limit=1)
print(f"{failed} failed")
sys.exit(1 if failed else 0)
PY
git -c user.name=eval -c user.email=eval@example.invalid add selection.md spec-guards
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Previous audit: Lemma 3 fixed, guard F-1-1"
