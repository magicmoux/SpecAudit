#!/usr/bin/env bash
# Local end-to-end test of a full audit of the demo, outside `claude plugin eval`, which refuses shell tools on platforms
# without a sandbox (Windows). It runs as you, in a throwaway repository under the temp directory.
# Usage: evals/local-e2e.sh [in-session|audit-session] [model]
set -uo pipefail
MODE=${1:-in-session}
MODEL=${2:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
WORK="$(mktemp -d "$TMP/sa-e2e-XXXX")"
cd "$WORK" && . "$PLUGIN/evals/_fixtures/demo-repo.sh"

OPTS="--max-iter 1 --keep --model $MODEL"
[ "$MODE" = in-session ] && OPTS="$OPTS --in-session --no-worktree"
echo "plugin $PLUGIN, mode $MODE, model $MODEL, repo $WORK"
claude -p "/spec-audit:start selection.md $OPTS" --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json \
  --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash > result.json 2> stderr.log

AUDIT="$WORK"
[ "$MODE" = audit-session ] && AUDIT="$(dirname "$WORK")/$(basename "$WORK")-audit-selection"
DIR="$AUDIT/spec-audit/selection"
fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
check "register written" "[ -f '$DIR/register.md' ]"
check "inventory written" "[ -f '$DIR/inventory.md' ]"
check "report written" "[ -f '$DIR/report.md' ]"
check "lemma 3 fixed" "grep -qE '^\*\*Lemma 3\.\*\*.*(min\(k, ?\|L\|\)|min\(k, ?n\)|k ≤ \|L\||k ≤ n)' '$AUDIT/selection.md'"
check "proposition 4 unchanged" "grep -qF 'P_k(L ++ M) = P_k(P_k(L) ++ P_k(M))' '$AUDIT/selection.md'"
check "guard red first recorded" "grep -qiE 'red' '$DIR/register.md'"
check "agent table filled" "grep -qE 'audit-selection-(reviewer|adjudicator)' '$DIR/register.md'"
check "internal revision committed" "git -C '$AUDIT' log --oneline | grep -q 'incomplete: audit in progress'"
check "report does not claim correctness" "! grep -qiE 'the document is correct' '$DIR/report.md'"
python -X utf8 -c "import json; d = json.load(open('result.json', encoding='utf-8')); print('cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'), '| denials', len(d.get('permission_denials', [])))" 2>/dev/null
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
