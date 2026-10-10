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
NOW=$(date +%s); LAUNCH="($(date -d "@$NOW" +%Y%m%d_%H%M 2>/dev/null || date -r "$NOW" +%Y%m%d_%H%M)|$(date -d "@$((NOW + 60))" +%Y%m%d_%H%M 2>/dev/null || date -r "$((NOW + 60))" +%Y%m%d_%H%M))"  # this minute or the next
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
check "guard red first recorded" "grep -qiwE 'red' '$DIR/register.md'"
check "agent table filled" "grep -qE 'audit-selection-(reviewer|adjudicator)' '$DIR/register.md'"
# git log --grep rather than a pipe into grep -q: under pipefail, grep -q exits at the first match and git log's SIGPIPE fails the check.
check "internal revision committed" "[ -n \"\$(git -C '$AUDIT' log --oneline -F --grep 'incomplete: audit in progress')\" ]"
# The results folder comes back to the root of the original repository at closing (--keep applies "Keep the worktree"),
# named by the launch time of the command, which this script takes just before launching.
RES="$(ls -d "$WORK"/SpecAudit-*/ 2>/dev/null | head -1)"
check "results folder named by launch time" "echo '$RES' | grep -qE '/SpecAudit-$LAUNCH(-[0-9]+)?/\$'"
check "results README with contents" "grep -q 'source/' '${RES}README.md' && grep -q 'resources/' '${RES}README.md'"
BASE="$(git -C "$WORK" rev-list --max-parents=0 HEAD | cut -c1-7)"  # the demo repository has a single starting commit
check "results README identifies the base commit" "grep -qF '$BASE' '${RES}README.md'"
check "original source kept unfixed" "grep -qF '|P_k(L)| = k.' '${RES}source/selection.md'"
check "report and patch in results" "[ -f '${RES}report.md' ] && [ -f '${RES}resources/corrections.patch' ]"
check "no runner cache in results" "[ -z \"\$(find '$RES' -name __pycache__ -o -name .pytest_cache)\" ]"
check "report does not claim correctness" "! grep -qiE 'the document is correct' '$DIR/report.md'"
python -X utf8 -c "import json; d = json.load(open('result.json', encoding='utf-8')); print('cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'), '| denials', len(d.get('permission_denials', [])))" 2>/dev/null
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
