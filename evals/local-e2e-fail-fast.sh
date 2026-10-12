#!/usr/bin/env bash
# --fail-fast on the demo (evals/_fixtures/selection.md): one detection wave, the candidates confirmed from the most
# upstream, and a stop at the first confirmed error. It checks that the error reported is a root (Lemma 3 or Example 6,
# never their consequence Corollary 5), that the document is unchanged and no fix committed, and that the report's
# "First error" section gives the proposed fix of the statement and the results the error may affect.
# Usage: evals/local-e2e-fail-fast.sh [in-session|audit-session] [model]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
MODE=${1:-audit-session}
MODEL=${2:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
WORK="$(mktemp -d "$TMP/sa-ff-XXXX")"
cd "$WORK" && . "$PLUGIN/evals/_fixtures/demo-repo.sh"

OPTS="--fail-fast --keep --model $MODEL"
[ "$MODE" = in-session ] && OPTS="$OPTS --in-session --no-worktree"
echo "plugin $PLUGIN, mode $MODE, model $MODEL, repo $WORK"
claude -p "/spec-audit:start selection.md $OPTS --account $ACCOUNT $SPECAUDIT_E2E_PAUSE" --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json \
  --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash > result.json 2> stderr.log

AUDIT="$WORK"
[ "$MODE" = audit-session ] && AUDIT="$(dirname "$WORK")/$(basename "$WORK")-audit-selection"
DIR="$AUDIT/spec-audit/selection"
REG="$DIR/register.md"
# The "First error" section of the report, alone.
FIRST="$(awk '/^## First error/{f=1;next} /^## /{f=0} f' "$DIR/report.md" 2>/dev/null)"
fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
check "register and report written" "[ -f '$REG' ] && [ -f '$DIR/report.md' ]"
check "fail-fast recorded" "grep -qiE 'fail-fast *= *yes' '$REG'"
check "one detection wave, not saturated" "grep -qiE 'not saturated' '$REG'"
check "report has a First error section" "[ -n \"\$FIRST\" ]"
check "the error reported is a root" "printf '%s' \"\$FIRST\" | head -5 | grep -qE 'Lemma 3|Example 6'"
check "not its consequence" "! printf '%s' \"\$FIRST\" | head -3 | grep -qE 'Corollary 5'"
check "proposed fix, not applied" "printf '%s' \"\$FIRST\" | grep -qiE 'not applied'"
check "results it may affect" "printf '%s' \"\$FIRST\" | grep -qE 'Corollary 5|Algorithm 7|Conclusion|Example 6'"
check "an executed counterexample" "[ -n \"\$(find '$AUDIT-scratch' '$DIR/scratch' -path '*adjudicator*' -name '*.py' 2>/dev/null)\" ]"
check "document unchanged" "cmp -s '$AUDIT/selection.md' '$PLUGIN/evals/_fixtures/selection.md'"
check "no fix committed" "[ -z \"\$(git -C '$AUDIT' log --oneline -F --grep 'fixed [incomplete')\" ]"
check "stop commit" "[ -n \"\$(git -C '$AUDIT' log --oneline -F --grep 'stopped at first error')\" ]"
RES="$(ls -d "$WORK"/SpecAudit-*/ 2>/dev/null | head -1)"
check "results folder with the report, no fixed copy" "[ -f '${RES}report.md' ] && [ ! -e '${RES}selection.fixed.md' ]"
check "index outcome" "grep -qi 'first error' '$WORK/SPECAUDITS.md'"
"$PY" -X utf8 -c "import json; d = json.load(open('result.json', encoding='utf-8')); print('cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'))" 2>/dev/null
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
