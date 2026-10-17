#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
# An audit whose target is a folder: docs/ holds selection.md and sums.md, audited together with --auto. It checks that
# the folder stands for the documents in it (both listed in the register, each fixed as its own errors require, the
# true statements kept), that the index names the folder as the audited object, and that the results folder holds the
# original and the fixed copy of each document, with a replay red on the originals and green on the fixed copies.
# Usage: evals/local-e2e-folder.sh [model]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
MODEL=${1:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
# On Windows, $TEMP is C:\Users\...\Temp: normalize it to C:/..., the form the audit session records, and pick an
# interpreter that runs, since python3 may be the Microsoft Store stub there.
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
WORK="$(mktemp -d "$TMP/sa-folder-XXXX")"
cd "$WORK" && mkdir docs && cp "$PLUGIN/evals/_fixtures/selection.md" "$PLUGIN/evals/_fixtures/sums.md" docs/
bash "$PLUGIN/evals/_fixtures/write-arch.sh" docs/ > SPECAUDIT_ARCH.md
git init -q
git -c user.name=eval -c user.email=eval@example.invalid add docs SPECAUDIT_ARCH.md
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Demo specifications"
echo "plugin $PLUGIN, model $MODEL, repo $WORK"

claude -p "/spec-audit:start docs/ --auto --max-passes 2 --keep --model $MODEL --account $ACCOUNT $SPECAUDIT_E2E_PAUSE" --plugin-dir "$PLUGIN" --model "$MODEL" \
  --output-format json --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash \
  > result.json 2> stderr.log

AUDIT="$(dirname "$WORK")/$(basename "$WORK")-audit-docs"
DIR="$AUDIT/spec-audit/docs"
RES="$(ls -d "$WORK"/SpecAudit-*/ 2>/dev/null | head -1)"
fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
check "one audit for the folder (slug docs)" "[ -f '$DIR/register.md' ] && [ -f '$DIR/report.md' ]"
check "register lists both documents" "grep -qF 'selection.md' '$DIR/register.md' && grep -qF 'sums.md' '$DIR/register.md'"
check "selection: Lemma 3 fixed" "grep -qE '^\\*\\*Lemma 3\\.\\*\\*.*(min\\(k, ?\\|L\\|\\)|min\\(k, ?n\\)|k ≤ \\|L\\||k ≤ n)' '$AUDIT/docs/selection.md'"
check "selection: Proposition 4 unchanged" "grep -qF 'P_k(L ++ M) = P_k(P_k(L) ++ P_k(M))' '$AUDIT/docs/selection.md'"
check "sums: Proposition 3 fixed" "grep -qE '^\\*\\*Proposition 3\\.\\*\\*.*n ?\\(n ?\\+ ?1\\) ?/ ?2' '$AUDIT/docs/sums.md'"
check "sums: Lemma 2 kept" "grep -qF 'O(n) = n²' '$AUDIT/docs/sums.md'"
check "originals untouched (keep)" "cmp -s '$WORK/docs/selection.md' '$PLUGIN/evals/_fixtures/selection.md' && cmp -s '$WORK/docs/sums.md' '$PLUGIN/evals/_fixtures/sums.md'"
check "index row names the folder, FINISHED" "grep -iE '^\\| \\[[^]]+\\]\\(#specaudit-' '$WORK/SPECAUDITS.md' | grep -F '\`docs/\`' | grep -q 'FINISHED'"
check "results folder holds both originals" "[ -n \"\$(find '${RES}source' -name selection.md)\" ] && [ -n \"\$(find '${RES}source' -name sums.md)\" ]"
check "results folder holds both fixed copies" "[ -n \"\$(find '$RES' -path '*/source' -prune -o -name selection.fixed.md -print)\" ] && [ -n \"\$(find '$RES' -path '*/source' -prune -o -name sums.fixed.md -print)\" ]"
check "replay red on the originals, green on the fixed copies" "(cd '$RES' && $PY resources/replay.py --on source >/dev/null && $PY resources/replay.py --on fixed >/dev/null)"
check "report sections in order, summary last" "$PY -c \"import re,sys; sys.exit(0 if re.search(r'## Result[\\s\\S]*## Cause graph[\\s\\S]*## Modified statements[\\s\\S]*## Errors[\\s\\S]*## Open points[\\s\\S]*## Corpus[\\s\\S]*## Scope of verification[\\s\\S]*## Consumption[\\s\\S]*## Branch and closing[\\s\\S]*## Summary of issues(?![\\s\\S]*\\n## )', open(sys.argv[1], encoding='utf-8').read()) else 1)\" '$DIR/report.md'"
$PY -X utf8 -c "import json; d = json.load(open('result.json', encoding='utf-8')); print('cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'))" 2>/dev/null
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
