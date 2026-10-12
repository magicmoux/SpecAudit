#!/usr/bin/env bash
# Pause and resume on a usage threshold, on the demo (evals/_fixtures/selection.md). A first launch with --pause-at 1
# pauses the audit as soon as the stream reports any usage, without waiting (--no-auto-resume); a second launch
# resumes it with --resume, under the tests' usage ceiling. It checks the pause (the request, the register suspended for the usage
# limit, no agent launched past it, every launched agent's prompt kept), then the resume (agents with a result not
# relaunched, the audit carried to its report).
# Usage: evals/local-e2e-pause.sh [model]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
MODEL=${1:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
WORK="$(mktemp -d "$TMP/sa-pause-XXXX")"
cd "$WORK" && . "$PLUGIN/evals/_fixtures/demo-repo.sh"
echo "plugin $PLUGIN, model $MODEL, repo $WORK"
run() {  # <options> <log name>
  claude -p "/spec-audit:start selection.md $1 --keep --model $MODEL --account $ACCOUNT" --plugin-dir "$PLUGIN" \
    --model "$MODEL" --output-format json --permission-mode dontAsk \
    --allowedTools Read Write Edit Glob Grep Skill Agent Bash > "$2.json" 2> "$2.err"
}
AUDIT="$(dirname "$WORK")/$(basename "$WORK")-audit-selection"
DIR="$AUDIT/spec-audit/selection"
REG="$DIR/register.md"
fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }

run "--max-passes 1 --pause-at 1 --no-auto-resume" first
check "pause requested" "[ -f '$AUDIT-scratch/pause-requested' ]"
check "register suspended for the usage limit" "grep -qiE 'state: *suspended \(usage limit' '$REG'"
check "no report yet" "[ ! -f '$DIR/report.md' ]"
# Agents' folders only (reviewer-, adjudicator-, probe-, reassess-…): the orchestrator keeps folders of its own there too.
check "every launched agent's prompt kept" "[ -n \"\$(find '$AUDIT-scratch' -name prompt.md 2>/dev/null)\" ] && [ -z \"\$(for d in \$(find '$AUDIT-scratch' -mindepth 2 -maxdepth 2 -type d -regextype posix-extended -regex '.*/iter-[0-9]+/(reviewer|adjudicator|probe|reassess)[^/]*'); do [ -f \"\$d/prompt.md\" ] || echo \"\$d\"; done)\" ]"
check "index entry still running" "grep -q 'RUNNING' '$WORK/SPECAUDITS.md'"
find "$AUDIT-scratch" -name result.md -printf '%p %T@\n' 2>/dev/null | sort > "$WORK/results-before.txt"

run "--resume --max-passes 1 $SPECAUDIT_E2E_PAUSE" second
check "resumed and carried to the report" "[ -f '$DIR/report.md' ]"
# An agent whose result.md was there before the resume is not run again: its result is not rewritten.
check "agents with a result not relaunched" "[ -z \"\$(join <(sort '$WORK/results-before.txt') <(find '$AUDIT-scratch' -name result.md -printf '%p %T@\n' | sort) | awk '\$2 != \$3')\" ]"
check "resume recorded" "grep -qiE 'resum' '$REG'"
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
