#!/usr/bin/env bash
# The architecture, end to end, outside `claude plugin eval` (which refuses shell tools without a sandbox, on Windows):
#   1. /spec-audit:init, run non-interactively (`claude -p`) on the fixture project _fixtures/arch-project/: the proposal
#      it prints gives each path its expected role, the Lean oracle its command, correspondence table and guard location,
#      and the revised paper its mapped pair; and it writes and commits nothing, since no question could be asked.
#   2. /spec-audit:start on the demo without SPECAUDIT_ARCH.md: it refuses, names /spec-audit:init, and leaves no
#      worktree, no register, no index entry and no commit.
# A few cents; runs as you, in throwaway repositories under the temp directory.
# Usage: evals/local-init.sh [model]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
MODEL=${1:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
text() { "$PY" -X utf8 -c "import json,sys; print(json.load(open(sys.argv[1], encoding='utf-8')).get('result', ''))" "$1"; }

# --- 1. init proposes, writes nothing --------------------------------------------------------------------------------
P="$(mktemp -d "$TMP/sa-init-XXXX")"
cp -r "$PLUGIN/evals/_fixtures/arch-project/." "$P/" && (cd "$P" && bash "$PLUGIN/evals/_fixtures/arch-repo.sh" --no-arch)
HEAD0="$(git -C "$P" rev-parse HEAD)"
echo "plugin $PLUGIN, model $MODEL, project $P"
(cd "$P" && claude -p "/spec-audit:init" --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json \
  --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Bash > result.json 2> stderr.log)
text "$P/result.json" > "$P/answer.md"
A="$P/answer.md"
check "init: artifacts/ audited, formal" "grep -qE '\`?artifacts/\`? *\\| *audited *\\| *formal' '$A'"
check "init: source/manuscript.md original" "grep -qE '\`?source/manuscript\\.md\`? *\\| *original\\b' '$A'"
check "init: source/references/ sources" "grep -qE '\`?source/references/\`? *\\| *sources\\b' '$A'"
check "init: mechanization/ oracle" "grep -qE '\`?mechanization/\`? *\\| *oracle\\b' '$A'"
check "init: the Lean command, run from the root" "grep -qF 'lake -d mechanization build' '$A'"
check "init: the correspondence table and the guard location" "grep -qF 'mechanization/CORRESPONDENCE.md' '$A' && grep -qF 'mechanization/Guards/' '$A'"
# The pair on one line, whatever joins it: a table row, "maps to", an arrow.
check "init: the mapped pair" "grep -qE 'artifacts/manuscript-revised\\.md.*mechanization/Selection|mechanization/Selection.*artifacts/manuscript-revised\\.md' '$A'"
check "init: README.md not given a role" "! grep -qE '^\\| *\`?README\\.md\`? *\\|' '$A'"
# Any wording of it: "not written", "haven't written" (straight or curly apostrophe), "nothing was written", "wrote nothing"…
check "init: says nothing was written" "grep -qiE '(not|n.{1,3}t) (yet )?(been )?written|nothing (was |has been )?written|did ?n.{0,3}t write|wrote nothing|without writing|no file' '$A'"
check "init: no SPECAUDIT_ARCH.md written" "[ ! -e '$P/SPECAUDIT_ARCH.md' ]"
check "init: no commit" "[ \"\$(git -C '$P' rev-parse HEAD)\" = '$HEAD0' ]"

# --- 2. start refuses without the file -------------------------------------------------------------------------------
D="$(mktemp -d "$TMP/sa-noarch-XXXX")"
(cd "$D" && . "$PLUGIN/evals/_fixtures/demo-repo.sh" && git -c user.name=eval -c user.email=eval@example.invalid rm -q SPECAUDIT_ARCH.md \
  && git -c user.name=eval -c user.email=eval@example.invalid commit -qm "No architecture")
HEAD1="$(git -C "$D" rev-parse HEAD)"
(cd "$D" && claude -p "/spec-audit:start selection.md --max-passes 1 --keep --model $MODEL --account $ACCOUNT $SPECAUDIT_E2E_PAUSE" \
  --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json \
  --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash > result.json 2> stderr.log)
text "$D/result.json" > "$D/answer.md"
check "start: refuses and names /spec-audit:init" "grep -qF '/spec-audit:init' '$D/answer.md' && grep -qF 'SPECAUDIT_ARCH.md' '$D/answer.md'"
check "start: no worktree, no branch" "[ ! -d '$D-audit-selection' ] && [ -z \"\$(git -C '$D' branch --list 'audit/*')\" ]"
check "start: no register, no index entry, no results folder" "[ ! -e '$D/spec-audit' ] && [ ! -e '$D/SPECAUDITS.md' ] && [ -z \"\$(ls -d '$D'/SpecAudit-* 2>/dev/null)\" ]"
check "start: no commit" "[ \"\$(git -C '$D' rev-parse HEAD)\" = '$HEAD1' ]"

for r in "$P" "$D"; do
  "$PY" -X utf8 -c "import json,sys; d = json.load(open(sys.argv[1], encoding='utf-8')); print(sys.argv[2], 'cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'))" "$r/result.json" "$(basename "$r")" 2>/dev/null
done
echo "$fails failure(s); artifacts in $P and $D"
exit $((fails > 0))
