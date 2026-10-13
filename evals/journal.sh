#!/usr/bin/env bash
# Test of the audit session's hook, skills/start/references/journal.py, on synthetic hook events: one agent at a time
# (--lock): a launch is forced to the foreground, a second launch while the first has not returned is refused and leaves
# nothing in its scratch directory, the return releases the lock, a lock whose agent ended without its release is
# stale, and a launch refused by a pause releases it; and of evals/_fixtures/serial_check.py, which reads the journals
# an audit leaves to tell whether two agents overlapped. No model, no network. Usage: evals/journal.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
JOURNAL="$ROOT/skills/start/references/journal.py"
SERIAL="$ROOT/evals/_fixtures/serial_check.py"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
TMP="$(mktemp -d "${TEMP:-${TMPDIR:-/tmp}}/sa-journal-XXXX")"
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
S="$TMP/scratch"; LOCK="$S/agent-running"; mkdir -p "$S"

fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
# hook <event json> [extra args]: runs the hook, keeps its stdout, stderr and exit code
hook() { local ev="$1"; shift; printf '%s' "$ev" | "$PY" "$JOURNAL" --lock "$LOCK" "$@" > "$TMP/out" 2> "$TMP/err"; echo $? > "$TMP/code"; }
launch() {  # launch <name> [background]: the orchestrator launches the agent whose scratch directory is $S/<name>
  "$PY" -c "import json,sys; print(json.dumps({'hook_event_name': 'PreToolUse', 'tool_name': 'Agent', 'tool_input': {'description': sys.argv[1], 'prompt': 'Review it. Scratch directory: ' + sys.argv[2] + '/' + sys.argv[1], 'run_in_background': sys.argv[3] == 'bg'}}))" "$1" "$S" "${2:-fg}"
}
returned() { printf '{"hook_event_name": "%s", "tool_name": "Agent", "tool_input": {}}' "${1:-PostToolUse}"; }
code() { cat "$TMP/code"; }

hook "$(launch reviewer-a bg)"
check "first launch allowed" "[ \"\$(code)\" = 0 ]"
check "forced to the foreground" "$PY -c \"import json,sys; u=json.load(open(sys.argv[1]))['hookSpecificOutput']['updatedInput']; sys.exit(u['run_in_background'] is not False)\" '$TMP/out'"
check "lock names the running agent" "grep -qF '$S/reviewer-a' '$LOCK/scratch'"
check "its prompt kept" "[ -f '$S/reviewer-a/prompt.md' ]"

hook "$(launch reviewer-b)"
check "second launch refused while the first runs" "[ \"\$(code)\" = 2 ] && grep -qi 'one agent at a time' '$TMP/err' && grep -qF 'reviewer-a' '$TMP/err'"
check "refused launch leaves nothing in its scratch directory" "[ ! -e '$S/reviewer-b/prompt.md' ]"

hook "$(returned)"
check "return releases the lock" "[ ! -e '$LOCK' ]"
hook "$(launch reviewer-b)"
check "next launch allowed once the first returned" "[ \"\$(code)\" = 0 ] && [ -f '$S/reviewer-b/prompt.md' ]"

# reviewer-b ends (its result.md, as SubagentStop writes it) but the return is never seen: the lock is stale.
echo "verdict" > "$S/reviewer-b/result.md"
hook "$(launch adjudicator-F-1-1)"
check "stale lock taken over once its agent has a result" "[ \"\$(code)\" = 0 ] && grep -qF 'adjudicator-F-1-1' '$LOCK/scratch'"
hook "$(returned PostToolUseFailure)"
check "a failed call releases the lock too" "[ ! -e '$LOCK' ]"

echo '{"window": "session", "utilization": 0.9, "resumeAtLocal": "12:00"}' > "$S/pause-requested"
hook "$(launch adjudicator-F-1-2)" --stream "$TMP/none.jsonl" --flag "$S/pause-requested"
check "launch refused by a pause" "[ \"\$(code)\" = 2 ] && grep -q '^paused: usage limit' '$TMP/err'"
check "the refused launch does not hold the lock" "[ ! -e '$LOCK' ]"
rm -f "$S/pause-requested"

printf '{"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"prompt": "Scratch directory: %s/x"}}' "$S" \
  | "$PY" "$JOURNAL" > "$TMP/out" 2>&1
check "without --lock, a launch is left as written" "[ ! -s '$TMP/out' ] && [ ! -e '$LOCK' ]"

# serial_check.py on journals: disjoint runs pass, a launch before the previous agent's stop fails.
J="$TMP/journals"; mkdir -p "$J/a" "$J/b" "$J/c"
rec() { printf '{"t": "2026-10-13T10:%s", "event": "%s"}\n' "$2" "$3" >> "$J/$1/journal.jsonl"; }
rec a 00:00 launch; rec a 01:00 stop; rec b 01:00 launch; rec b 02:00 stop; rec c 02:30 launch; rec c 03:00 stop
check "serial runs pass" "$PY '$SERIAL' '$J' > '$TMP/serial.log'"
rec a 02:45 launch
check "an overlap is reported" "! $PY '$SERIAL' '$J' > '$TMP/serial.log' && grep -q OVERLAP '$TMP/serial.log'"
# A journal whose stop record is missing ends when its agent's result.md was written.
J2="$TMP/journals2"; mkdir -p "$J2/x" "$J2/y"
printf '{"t": "2000-01-01T10:00:00", "event": "launch"}\n' > "$J2/x/journal.jsonl"; touch -d '2000-01-01 10:01:00' "$J2/x/result.md"
printf '{"t": "2000-01-01T10:02:00", "event": "launch"}\n{"t": "2000-01-01T10:03:00", "event": "stop"}\n' > "$J2/y/journal.jsonl"
check "a missing stop record falls back on result.md" "$PY '$SERIAL' '$J2' > '$TMP/serial2.log'"
# The stream: an Agent call launched before the previous one returned.
mkdir -p "$J2/launch"
u() { printf '{"type": "assistant", "parent_tool_use_id": null, "message": {"content": [{"type": "tool_use", "id": "%s", "name": "Agent", "input": {"description": "%s"}}]}}\n' "$1" "$1"; }
r() { printf '{"type": "user", "parent_tool_use_id": null, "message": {"content": [{"type": "tool_result", "tool_use_id": "%s", "content": "done"}]}}\n' "$1"; }
{ u a; r a; u b; r b; } > "$J2/launch/stream.jsonl"
check "stream: launches one after the other pass" "$PY '$SERIAL' '$J2' > '$TMP/serial3.log'"
{ u a; u b; r a; r b; } > "$J2/launch/stream.jsonl"
check "stream: a launch before the previous result is an overlap" "! $PY '$SERIAL' '$J2' > '$TMP/serial4.log' && grep -q 'OVERLAP stream' '$TMP/serial4.log'"

echo "$fails failure(s)"
exit $((fails > 0))
