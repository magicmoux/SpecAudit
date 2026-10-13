#!/usr/bin/env bash
# Two audits launched at the same moment from the same repository, on two different documents, with opposite
# scenarios: selection.md without --auto (a critical fix stays pending: partial, no fixed copy) and sums.md with --auto
# (its one false proposition is fixed, its true lemma kept: every error fixed, fixed copy). It checks that nothing is
# shared between them (worktrees, launch files, scratch roots, results folders), that both closings land in the
# original repository (two index rows, two results folders, no lost commit or leftover lock), and each verdict.
# Usage: evals/local-e2e-parallel.sh [model]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
. "$(dirname "$0")/_fixtures/consumption-check.sh"
MODEL=${1:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
# On Windows, $TEMP is C:\Users\...\Temp: normalize it to C:/..., the form the audit session records, and pick an
# interpreter that runs, since python3 may be the Microsoft Store stub there.
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
WORK="$(mktemp -d "$TMP/sa-par-XXXX")"
cd "$WORK" && . "$PLUGIN/evals/_fixtures/demo-repo.sh"
cp "$PLUGIN/evals/_fixtures/sums.md" .
bash "$PLUGIN/evals/_fixtures/write-arch.sh" selection.md sums.md > SPECAUDIT_ARCH.md
git -c user.name=eval -c user.email=eval@example.invalid add sums.md SPECAUDIT_ARCH.md
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Sums specification"
echo "plugin $PLUGIN, model $MODEL, repo $WORK"

launch() {  # <document> <options> <log name>
  claude -p "/spec-audit:start $1 $2 --keep --model $MODEL --account $ACCOUNT $SPECAUDIT_E2E_PAUSE" --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json \
    --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash > "$3.json" 2> "$3.err"
}
launch selection.md "--max-passes 1" result-selection &
A=$!
launch sums.md "--auto --max-passes 2" result-sums &
B=$!
wait $A; wait $B

fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
P=$(dirname "$WORK"); N=$(basename "$WORK")
WA="$P/$N-audit-selection"; WB="$P/$N-audit-sums"

# Nothing shared
check "two worktrees, one per document" "[ -d '$WA' ] && [ -d '$WB' ] && git -C '$WORK' worktree list | grep -q 'audit/selection' && git -C '$WORK' worktree list | grep -q 'audit/sums'"
check "launch files per audit" "[ -f '$WA-scratch/launch/protocol.md' ] && [ -f '$WB-scratch/launch/protocol.md' ] && [ -f '$WA-scratch/launch/agents.json' ] && [ -f '$WB-scratch/launch/agents.json' ]"
check "each register records its own scratch root" "grep -qF 'Scratch root: $WA-scratch' '$WA/spec-audit/selection/register.md' && grep -qF 'Scratch root: $WB-scratch' '$WB/spec-audit/sums/register.md'"
for R in "$WA/spec-audit/selection/register.md" "$WB/spec-audit/sums/register.md"; do
  check "preflight passed at the first attempt ($(basename "$(dirname "$R")"))" "grep -qiE 'Preflight: *passed[^|]*attempt 1\\b' '$R'"
  check "register records the launcher's session id ($(basename "$(dirname "$R")"))" "grep -qE '^- Session: .*[0-9a-f]{8}-[0-9a-f]{4}-' '$R' && ! grep -qF 'CLAUDE_SESSION_ID' '$R'"
done
for AUD in "$WA" "$WB"; do
  PROJ="$HOME/.claude/projects/$(echo "$AUD" | sed 's|[^A-Za-z0-9]|-|g')"
  REG=$(ls "$AUD"/spec-audit/*/register.md | head -1)
  check "every refusal recorded in $(basename "$AUD")" "[ \"\$($PY '$PLUGIN/evals/_fixtures/count_refusals.py' '$PROJ' 2>/dev/null | head -1 || echo 0)\" = \"\$(grep -oE '^- Refusals: *[0-9]+' '$REG' | grep -oE '[0-9]+\$' || echo 0)\" ]"
done

# Both closings in the original repository
FOLDERS=$(ls -d "$WORK"/SpecAudit-*/ 2>/dev/null | wc -l)
check "two results folders, distinct" "[ '$FOLDERS' -eq 2 ]"
# The name is reserved by mkdir in the original repository: no closing ever commits into the other's folder.
check "no closing committed into the other's folder" "[ -z \"\$(git -C '$WORK' log --format=%s | grep -i '^Revert')\" ]"
check "two index rows and two sections" "[ \"\$(grep -ciE '^\\| \\[[^]]+\\]\\(#specaudit-' '$WORK/SPECAUDITS.md' 2>/dev/null)\" -eq 2 ] && [ \"\$(grep -cE '^## SpecAudit-' '$WORK/SPECAUDITS.md')\" -eq 2 ]"
check "index row for selection.md" "grep -iE '^\\| \\[[^]]+\\]\\(#specaudit-' '$WORK/SPECAUDITS.md' | grep -q 'selection\\.md'"
check "index row for sums.md" "grep -iE '^\\| \\[[^]]+\\]\\(#specaudit-' '$WORK/SPECAUDITS.md' | grep -q 'sums\\.md'"
check "no leftover git lock" "[ ! -e '$WORK/.git/index.lock' ] && [ ! -e '$WORK/SPECAUDITS.md.lock' ]"
# Every commit of the index keeps the entries of the one before: a write from a stale read would erase the other
# audit's entry, even if a later commit put it back.
index_never_lost() {
  local prev="" cur c
  for c in $(git -C "$WORK" log --reverse --format=%h -- SPECAUDITS.md); do
    cur=$(git -C "$WORK" show "$c:SPECAUDITS.md" | grep -oE '^## SpecAudit-[0-9_-]+')
    if [ -n "$prev" ] && printf '%s\n' "$prev" | grep -qvxF -f <(printf '%s\n' "$cur"); then echo "  $c drops an entry"; return 1; fi
    prev="$cur"
  done
}
check "no index commit drops the other audit's entry" "index_never_lost"
check "original documents untouched (keep)" "cmp -s '$WORK/selection.md' '$PLUGIN/evals/_fixtures/selection.md' && cmp -s '$WORK/sums.md' '$PLUGIN/evals/_fixtures/sums.md'"
RA=$(grep -lF 'selection.md' "$WORK"/SpecAudit-*/README.md 2>/dev/null | head -1 | xargs -r dirname)
RB=$(grep -lF 'sums.md' "$WORK"/SpecAudit-*/README.md 2>/dev/null | grep -v "^${RA:-none}/" | head -1 | xargs -r dirname)
check "each folder holds only its own source" "[ -f '$RA/source/selection.md' ] && [ ! -e '$RA/source/sums.md' ] && [ -f '$RB/source/sums.md' ] && [ ! -e '$RB/source/selection.md' ]"

# Verdicts
for R in "$RA" "$RB"; do
  check "report sections in order, summary last ($(basename "$R"))" "$PY -c \"import re,sys; sys.exit(0 if re.search(r'## Result[\\s\\S]*## Cause graph[\\s\\S]*## Modified statements[\\s\\S]*## Errors[\\s\\S]*## Open points[\\s\\S]*## Corpus[\\s\\S]*## Scope of verification[\\s\\S]*## Consumption[\\s\\S]*## Branch and closing[\\s\\S]*## Summary of issues(?![\\s\\S]*\\n## )', open(sys.argv[1], encoding='utf-8').read()) else 1)\" '$R/report.md'"
done
# Each report's consumption is measured from its own audit session's streams, not the other's.
check "A: consumption total equals consumption.py on its streams" "consumption_matches '$RA/report.md' '$WA-scratch/launch'"
check "B: consumption total equals consumption.py on its streams" "consumption_matches '$RB/report.md' '$WB-scratch/launch'"
check "A: Lemma 3 fixed in its worktree" "grep -qE '^\\*\\*Lemma 3\\.\\*\\*.*(min\\(k, ?\\|L\\|\\)|min\\(k, ?n\\)|k ≤ \\|L\\||k ≤ n)' '$WA/selection.md'"
check "A: no fixed copy (critical fix pending)" "[ ! -e '$RA/selection.fixed.md' ]"
check "B: Proposition 3 fixed" "grep -qE '^\\*\\*Proposition 3\\.\\*\\*.*n ?\\(n ?\\+ ?1\\) ?/ ?2' '$WB/sums.md'"
check "B: Lemma 2 kept" "grep -qF 'O(n) = n²' '$WB/sums.md'"
check "B: fixed copy at the root of its folder" "[ -f '$RB/sums.fixed.md' ] && grep -qE 'n ?\\(n ?\\+ ?1\\) ?/ ?2' '$RB/sums.fixed.md'"
check "B: replay red on the original, green on the fixed copy" "(cd '$RB' && $PY resources/replay.py --on source >/dev/null && $PY resources/replay.py --on fixed >/dev/null)"

for r in result-selection result-sums; do
  $PY -X utf8 -c "import json; d = json.load(open('$r.json', encoding='utf-8')); print('$r cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'))" 2>/dev/null
done
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
