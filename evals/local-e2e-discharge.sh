#!/usr/bin/env bash
# Hypothesis discharge, end to end, on examples/discharge/block-search.md: Proposition 3 applies Lemma 2 to A ++ B
# without guaranteeing that it is sorted, and Theorem 6, named by the abstract, applies Proposition 3. It checks that
# the use edges are recorded, that a probe finds the gap with an executed counterexample, that the error is put on
# Proposition 3 rather than on the correct Lemma 2, that Theorem 6 enters the cause graph as a consequence,
# that the correct sibling Proposition 4 is left unchanged, and that the probes are recorded in the corpus's cache and
# reused: a new selection on the audited document takes the settled edge of the correct Corollary 8 from the cache.
# Usage: evals/local-e2e-discharge.sh [in-session|audit-session] [model] [audit options, default "--max-passes 1"]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
MODE=${1:-audit-session}
MODEL=${2:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
# On Windows, $TEMP is C:\Users\...\Temp: normalize it to C:/..., the form the audit session records, and pick an
# interpreter that runs, since python3 may be the Microsoft Store stub there.
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
WORK="$(mktemp -d "$TMP/sa-dis-XXXX")"
cd "$WORK" && cp "$PLUGIN/examples/discharge/block-search.md" . && git init -q \
  && git -c user.name=eval -c user.email=eval@example.invalid add block-search.md \
  && git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Example specification"

AUDIT_OPTS=${3:---max-passes 1}
OPTS="$AUDIT_OPTS --keep --model $MODEL"
[ "$MODE" = in-session ] && OPTS="$OPTS --in-session --no-worktree"
echo "plugin $PLUGIN, mode $MODE, model $MODEL, repo $WORK"
claude -p "/spec-audit:start block-search.md $OPTS --account $ACCOUNT $SPECAUDIT_E2E_PAUSE" --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json \
  --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash > result.json 2> stderr.log

AUDIT="$WORK"
[ "$MODE" = audit-session ] && AUDIT="$(dirname "$WORK")/$(basename "$WORK")-audit-block-search"
DIR="$AUDIT/spec-audit/block-search"
REG="$DIR/register.md"
fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
check "register, inventory and report written" "[ -f '$REG' ] && [ -f '$DIR/inventory.md' ] && [ -f '$DIR/report.md' ]"
check "edges recorded, Proposition 3 → Lemma 2 among them" "$PY -X utf8 -c \"import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8')); sys.exit(0 if any('Proposition 3' in e['user'] and 'Lemma 2' in e['used'] for e in d['edges']) else 1)\" '$DIR/edges.json'"
check "discharge section in the register" "grep -q '^## Hypothesis discharge' '$REG'"
check "a probe launched and recorded" "grep -qE 'audit-block-search-probe-E-' '$REG'"
check "a red probe" "awk '/^## Hypothesis discharge/{f=1;next} /^## /{f=0} f' '$REG' | grep -qw 'RED'"
check "an error found by a probe" "grep -qE '^- \*\*Origin\*\*:.*probe \((lifted from )?E-' '$REG'"
# Theorem 6 is reached either by lifting the probe of Proposition 3 or by the probe of its own use of Proposition 3.
check "Theorem 6 a consequence in the cause graph" "grep -qE 'F-[0-9]+-[0-9]+ → F-[0-9]+-[0-9]+[^;]*Theorem 6' '$REG'"
check "Lemma 2 unchanged" "grep -qF '**Lemma 2.** For every sorted list L and every integer v, bsearch(L, v) = true if and only if v ∈ L.' '$AUDIT/block-search.md'"
check "Proposition 4 unchanged" "grep -qF 'such that every element of A is at most every element of B, and every integer v, bsearch(A ++ B, v) = true if and only if v ∈ A or v ∈ B.' '$AUDIT/block-search.md'"
check "Proposition 3 fixed" "! grep -qF '**Proposition 3.** For all sorted lists A and B and every integer v, bsearch(A ++ B, v) = true if and only if v ∈ A or v ∈ B.' '$AUDIT/block-search.md'"
CORPUS="$(grep -oE '^- Corpus: [^,]+' "$REG" | sed 's/^- Corpus: //; s/`//g')"
# The cache may be empty: a probe whose edge the fix then changed describes texts that no longer exist.
check "probe cache written in the corpus" "$PY -X utf8 -c \"import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))\" '$AUDIT/${CORPUS:-spec-guards}/discharge.json'"
# A second audit would start with this selection: run it on a copy of the edges, from the audited worktree.
cp "$DIR/edges.json" "$WORK/edges-again.json"
check "settled probes reused from the cache" "(cd '$AUDIT' && $PY -X utf8 '$PLUGIN/skills/start/references/discharge.py' select '$WORK/edges-again.json' '${CORPUS:-spec-guards}/discharge.json' --strongest ad-hoc | grep -qE 'from the cache: [1-9]')"
check "cache committed" "[ -n \"\$(git -C '$AUDIT' log --oneline -- '${CORPUS:-spec-guards}/discharge.json')\" ]"
check "report says what discharge did" "grep -qi 'discharge' '$DIR/report.md'"
check "preflight passed at the first attempt" "grep -qiE 'Preflight: *passed[^|]*attempt 1\\b' '$REG'"
"$PY" -X utf8 -c "import json; d = json.load(open('result.json', encoding='utf-8')); print('cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'), '| denials', len(d.get('permission_denials', [])))" 2>/dev/null
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
