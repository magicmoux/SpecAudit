#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
# An agent killed in the middle of its work, on the demo (evals/_fixtures/selection.md). The audit is launched, and as
# soon as an agent has journaled a tool call but not ended, the launcher and the audit session are killed, as a crash
# would. Then --resume. It checks that the hooks kept the killed agent's prompt and journal without a result, and that
# the resume replaced it with the same prompt, in the same scratch directory, and carried the audit to its report.
# Usage: evals/local-e2e-kill.sh [model]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
[ -n "${SPECAUDIT_E2E_TRACE:-}" ] && { exec 2>> "$SPECAUDIT_E2E_TRACE"; set -x; }
trap 'echo "step: exit (status $?)"' EXIT
MODEL=${1:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
WORK="$(mktemp -d "$TMP/sa-kill-XXXX")"
cd "$WORK" && . "$PLUGIN/evals/_fixtures/demo-repo.sh"
echo "plugin $PLUGIN, model $MODEL, repo $WORK"
AUDIT="$(dirname "$WORK")/$(basename "$WORK")-audit-selection"
DIR="$AUDIT/spec-audit/selection"
REG="$DIR/register.md"
OPTS="--max-passes 1 --keep --model $MODEL --account $ACCOUNT $SPECAUDIT_E2E_PAUSE"
launch() {  # <options> <log name>
  claude -p "/spec-audit:start selection.md $1" --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json \
    --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash > "$2.json" 2> "$2.err"
}
fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }

# The launcher is started here, not in a subshell, so that its own process can be killed: killing the subshell of a
# function left the launcher alive, and it resumed the audit by itself, which is not what this test checks.
claude -p "/spec-audit:start selection.md $OPTS" --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json   --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash > first.json 2> first.err &
LAUNCHER=$!
echo "step: launched (pid $LAUNCHER), waiting for an agent in the middle of its work"
VICTIM=""
for i in $(seq 1 240); do  # up to 20 minutes
  for j in "$AUDIT-scratch"/iter-*/*/journal.jsonl; do
    [ -f "$j" ] && grep -q '"tool"' "$j" && [ ! -f "$(dirname "$j")/result.md" ] && VICTIM="$(dirname "$j")" && break 2
  done
  kill -0 "$LAUNCHER" 2>/dev/null || break
  sleep 5
done
check "an agent caught in the middle of its work" "[ -n '$VICTIM' ]"
echo "step: killing the launcher, then the audit session and its agents"
WINPID="$(cat "/proc/$LAUNCHER/winpid" 2>/dev/null)"
if [ -n "$WINPID" ]; then taskkill //PID "$WINPID" //T //F >/dev/null 2>&1
elif kill -0 "$LAUNCHER" 2>/dev/null; then kill -9 "$LAUNCHER" 2>/dev/null; fi
# The audit session: the claude process whose command line names this audit's launch folder. Only claude.exe, and never
# this script's own processes: the filter's text is in PowerShell's own command line too.
if command -v powershell >/dev/null 2>&1; then
  powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'claude.exe' -and \$_.CommandLine -like '*$(basename "$AUDIT")-scratch*launch*' } | ForEach-Object { taskkill /PID \$_.ProcessId /T /F | Out-Null }" >/dev/null 2>&1 || true
else
  pkill -f "claude.*$(basename "$AUDIT")-scratch/launch" 2>/dev/null || true
fi
# Not `wait`: on Windows, once the launcher's process tree is killed, Git Bash's own stub for it may never return,
# and the test hung there. Give it a few seconds, then end it.
for i in $(seq 1 15); do kill -0 "$LAUNCHER" 2>/dev/null || break; sleep 1; done
# Only if it is still there: Git Bash may give the pid of a process already gone to another one, and a kill sent to
# that pid ended this test itself.
kill -0 "$LAUNCHER" 2>/dev/null && kill -9 "$LAUNCHER" 2>/dev/null
sleep 5
check "nothing of this audit still running" "! powershell -NoProfile -Command \"Get-CimInstance Win32_Process | Where-Object { \\$_.Name -eq 'claude.exe' -and \\$_.CommandLine -like '*$(basename "$AUDIT")-scratch*launch*' } | ForEach-Object { 'alive' }\" 2>/dev/null | grep -q alive"
echo "step: checking the killed agent"
PROMPT_SUM="$(md5sum "$VICTIM/prompt.md" 2>/dev/null | cut -d' ' -f1)"
check "killed agent: prompt and journal kept, no result" "[ -f '$VICTIM/prompt.md' ] && grep -q '\"tool\"' '$VICTIM/journal.jsonl' && [ ! -f '$VICTIM/result.md' ]"

echo "step: resuming"
launch "--resume $OPTS" second
check "resumed and carried to the report" "[ -f '$DIR/report.md' ]"
check "killed agent relaunched in the same scratch directory, with its result" "[ -f '$VICTIM/result.md' ]"
check "same prompt" "[ \"\$(md5sum '$VICTIM/prompt.md' | cut -d' ' -f1)\" = '$PROMPT_SUM' ]"
[ -f "$VICTIM/prompt.rewritten.md" ] && echo "note: the orchestrator rewrote the prompt; the hook sent the original (see prompt.rewritten.md)"
check "replacement recorded" "grep -qiE 'replaced by' '$REG'"
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
