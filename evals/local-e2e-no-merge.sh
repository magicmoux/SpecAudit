#!/usr/bin/env bash
# The closing without --keep, which no other script reaches: an audit in a claude -p session cannot ask the closing
# question and applies its non-interactive rule, "Keep the branch". With --auto and two passes, every confirmed error
# can be fixed, the outcome where a merge would be most tempting. It checks that the audit never merges: the branch
# audit/<stamp> kept with its final commit, no merge commit and no fix on the original branch, the original document
# untouched; and that the results folder and the index entry came back to the original branch, naming that branch and
# its final commit, with the corpus green on the fixed copy.
# Usage: evals/local-e2e-no-merge.sh [model]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
MODEL=${1:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
# On Windows, $TEMP is C:\Users\...\Temp: normalize it to C:/..., the form the audit session records, and pick an
# interpreter that runs, since python3 may be the Microsoft Store stub there.
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
WORK="$(mktemp -d "$TMP/sa-nomerge-XXXX")"
cd "$WORK" && . "$PLUGIN/evals/_fixtures/demo-repo.sh"
echo "plugin $PLUGIN, model $MODEL, repo $WORK"
AUDIT="$(dirname "$WORK")/$(basename "$WORK")-audit-selection"
ROOT_COMMIT="$(git rev-list --max-parents=0 HEAD)"

claude -p "/spec-audit:start selection.md --auto --max-passes 2 --model $MODEL --account $ACCOUNT $SPECAUDIT_E2E_PAUSE" --plugin-dir "$PLUGIN" --model "$MODEL" \
  --output-format json --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash > result.json 2> stderr.log

RES="$(ls -d "$WORK"/SpecAudit-*/ 2>/dev/null | head -1)"; NAME=$(basename "$RES"); BR="audit/${NAME#SpecAudit-}"
FINAL="$(git -C "$WORK" rev-parse -q --verify "refs/heads/$BR" 2>/dev/null)"
fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
check "branch audit/<stamp> kept, with the results folder's stamp" "[ -n '$FINAL' ] && [ -d '$AUDIT' ]"
check "closing applied Keep the branch (no question could be asked)" "grep -qiE 'keep the branch' '$AUDIT/spec-audit/selection/register.md'"
check "branch ends with its final commit" "git -C '$WORK' log -1 --format=%s '$BR' | grep -qi 'final'"
check "no merge commit on the original branch" "[ -z \"\$(git -C '$WORK' log --merges --format=%h)\" ]"
check "final commit not in the original branch" "! git -C '$WORK' merge-base --is-ancestor '$FINAL' HEAD"
check "original document untouched" "cmp -s '$WORK/selection.md' '$PLUGIN/evals/_fixtures/selection.md'"
check "original branch took only the results folder and the index" "[ -z \"\$(git -C '$WORK' log --format= --name-only '$ROOT_COMMIT..HEAD' | grep -v '^\$' | grep -vE '^(SPECAUDITS\\.md|$NAME/)')\" ]"
check "results folder committed on the original branch" "git -C '$WORK' ls-files --error-unmatch '$NAME/README.md' >/dev/null 2>&1"
check "README names the branch and its final commit" "grep -qF '$BR' '${RES}README.md' && grep -qF '${FINAL:0:7}' '${RES}README.md'"
check "index entry FINISHED, naming the branch and its final commit" "awk -v id='## $NAME' '\$0==id{f=1;next} /^## /{f=0} f' '$WORK/SPECAUDITS.md' > '$WORK/entry.md' && grep -qF '$BR' '$WORK/entry.md' && grep -qF '${FINAL:0:7}' '$WORK/entry.md' && grep -iE '^\\| \\[[^]]+\\]\\(#$NAME\\)' '$WORK/SPECAUDITS.md' | grep -q FINISHED"
check "report proposes no merge nor pull request" "! grep -iE '(merge|pull request)' '${RES}report.md' | grep -viE '\\b(never|not|no|nor|user|your own|themselves|by their)\\b' | grep -q ."
check "corpus green on the fixed copy" "(cd '$RES' && $PY resources/replay.py --on fixed >/dev/null)"
check "no leftover git lock" "[ ! -e '$WORK/.git/index.lock' ] && [ ! -e '$WORK/SPECAUDITS.md.lock' ]"

$PY -X utf8 -c "import json; d = json.load(open('result.json', encoding='utf-8')); print('cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'))" 2>/dev/null
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
