#!/usr/bin/env bash
# The "Accept and merge" closing, which no non-interactive run reaches on its own: an audit without --keep, in a
# claude -p session, cannot ask the closing question and applies "Keep the worktree"; the same session is then resumed
# with the answer a user would give on coming back, "Accept and merge". It checks that the kept audit was left intact,
# then that the merge went through its safety checks: the audit branch merged into the original branch, the worktree
# and the branch removed, the fixed document at the root, Proposition 4 unchanged, and one index entry for the audit,
# updated rather than duplicated.
# Usage: evals/local-e2e-merge.sh [model]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
MODEL=${1:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
# On Windows, $TEMP is C:\Users\...\Temp: normalize it to C:/..., the form the audit session records, and pick an
# interpreter that runs, since python3 may be the Microsoft Store stub there.
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
WORK="$(mktemp -d "$TMP/sa-merge-XXXX")"
cd "$WORK" && . "$PLUGIN/evals/_fixtures/demo-repo.sh"
echo "plugin $PLUGIN, model $MODEL, repo $WORK"
AUDIT="$(dirname "$WORK")/$(basename "$WORK")-audit-selection"
TOOLS=(--permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash)

# --auto and two iterations, so that every confirmed error can be fixed and "Accept" is an option the closing offers.
claude -p "/spec-audit:start selection.md --auto --max-passes 2 --model $MODEL --account $ACCOUNT $SPECAUDIT_E2E_PAUSE" --plugin-dir "$PLUGIN" --model "$MODEL" \
  --output-format json "${TOOLS[@]}" > result-audit.json 2> stderr-audit.log
SID="$($PY -c "import json; print(json.load(open('result-audit.json', encoding='utf-8')).get('session_id', ''))" 2>/dev/null)"

fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
check "first run: worktree kept (no question could be asked)" "[ -d '$AUDIT' ] && git -C '$WORK' branch --list 'audit/selection' | grep -q ."
check "first run: document untouched on the original branch" "cmp -s '$WORK/selection.md' '$PLUGIN/evals/_fixtures/selection.md'"
check "first run: index entry FINISHED" "grep -iE '^\\| \\[[^]]+\\]\\(#specaudit-' '$WORK/SPECAUDITS.md' | grep -q 'FINISHED'"
check "first run: session id known" "[ -n '$SID' ]"

claude -p "Accept and merge" --resume "$SID" --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json "${TOOLS[@]}" \
  > result-merge.json 2> stderr-merge.log

RES="$(ls -d "$WORK"/SpecAudit-*/ 2>/dev/null | head -1)"; NAME=$(basename "$RES")
check "audit branch merged into the original branch" "git -C '$WORK' log --merges --format=%s | grep -qi 'selection\\|audit'"
check "worktree removed" "[ ! -d '$AUDIT' ] && ! git -C '$WORK' worktree list | grep -q 'audit-selection'"
check "audit branch removed" "[ -z \"\$(git -C '$WORK' branch --list 'audit/selection')\" ]"
check "Lemma 3 fixed at the root" "grep -qE '^\\*\\*Lemma 3\\.\\*\\*.*(min\\(k, ?\\|L\\|\\)|min\\(k, ?n\\)|k ≤ \\|L\\||k ≤ n)' '$WORK/selection.md'"
check "Proposition 4 unchanged" "grep -qF 'P_k(L ++ M) = P_k(P_k(L) ++ P_k(M))' '$WORK/selection.md'"
check "results folder on the original branch" "[ -n '$RES' ] && git -C '$WORK' ls-files --error-unmatch '${NAME}/README.md' >/dev/null 2>&1"
check "one index entry for the audit" "[ \"\$(grep -ciE '^\\| \\[[^]]+\\]\\(#specaudit-' '$WORK/SPECAUDITS.md')\" -eq 1 ] && [ \"\$(grep -cE '^## SpecAudit-' '$WORK/SPECAUDITS.md')\" -eq 1 ]"
check "index section records the merge" "awk -v id='## $NAME' '\$0==id{f=1;next} /^## /{f=0} f' '$WORK/SPECAUDITS.md' | grep -iE '^\\| Closing \\|' | grep -qi 'merge'"
check "register closed" "grep -qiE 'state:? *\\**closed' '$WORK/spec-audit/selection/register.md'"
check "corpus green on the merged document" "(cd '$RES' && $PY resources/replay.py --on fixed >/dev/null)"
check "no leftover git lock" "[ ! -e '$WORK/.git/index.lock' ]"
check "nothing left uncommitted" "[ -z \"\$(git -C '$WORK' status --porcelain --untracked-files=no)\" ]"

for r in result-audit result-merge; do
  $PY -X utf8 -c "import json; d = json.load(open('$r.json', encoding='utf-8')); print('$r cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'))" 2>/dev/null
done
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
