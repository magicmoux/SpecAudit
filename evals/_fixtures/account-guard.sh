#!/usr/bin/env bash
# Sourced by every script that launches `claude`: each run is billed to the account the claude CLI is logged into,
# which may not be the one of the session that starts the script. Refuses to go on unless SPECAUDIT_E2E_ACCOUNT names
# that account's e-mail. To run on another account, log it in under its own configuration folder once
# (CLAUDE_CONFIG_DIR="$HOME/.claude-perso" claude auth login), then pass the same CLAUDE_CONFIG_DIR to the script.
# A script started from a Claude session (the desktop app, an Agent SDK host) inherits that session's credentials, which
# win over CLAUDE_CONFIG_DIR: every run would be billed to the session's account while `claude auth status` names the
# folder's. Remove them first, for this script and every claude it starts (skills/start/references/account.py clean-env).
for _v in $(python3 "$(dirname "${BASH_SOURCE[0]}")/../../skills/start/references/account.py" clean-env 2>/dev/null             || python "$(dirname "${BASH_SOURCE[0]}")/../../skills/start/references/account.py" clean-env); do
  [ "$_v" = -u ] || unset "$_v"
done
ACCOUNT="$(claude auth status 2>/dev/null | sed -n 's/.*"email": *"\([^"]*\)".*/\1/p' | head -1)"
CONFIG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
if [ -z "$ACCOUNT" ] || [ "${SPECAUDIT_E2E_ACCOUNT:-}" != "$ACCOUNT" ]; then
  echo "account guard: the claude CLI (config $CONFIG) is logged in as '${ACCOUNT:-nobody}'," >&2
  echo "  and SPECAUDIT_E2E_ACCOUNT is '${SPECAUDIT_E2E_ACCOUNT:-unset}': nothing launched." >&2
  echo "  To run on that account: SPECAUDIT_E2E_ACCOUNT=$ACCOUNT $0 ..." >&2
  echo "  To run on another one: CLAUDE_CONFIG_DIR=<its config folder> SPECAUDIT_E2E_ACCOUNT=<its e-mail> $0 ..." >&2
  exit 3
fi
echo "account: $ACCOUNT (config $CONFIG)"

# Usage ceiling: the tests may spend at most SPECAUDIT_E2E_MARGIN points of the account's usage above what it used when
# the batch started (default 1; "session=1,week=2" sets each window),
# in the session window and in the week. The ceiling is computed once per session window, by a tiny request whose stream
# gives the current usage, and shared by every script started before that window resets (a file in the temp folder);
# SPECAUDIT_E2E_CEILING="session=N,week=N" sets it instead. Every audit a test launches gets it as --pause-at, with
# --no-auto-resume: past the ceiling, the audit pauses and the test ends, rather than spending on.
GUARD_PY=python3; "$GUARD_PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || GUARD_PY=python
GUARD_USAGE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../skills/start/references" && pwd)/usage.py"
GUARD_TMP="${TEMP:-${TMPDIR:-/tmp}}"
command -v cygpath >/dev/null 2>&1 && GUARD_TMP="$(cygpath -m "$GUARD_TMP")"
GUARD_FILE="$GUARD_TMP/specaudit-e2e-ceiling-$(printf '%s' "$ACCOUNT" | tr -c 'A-Za-z0-9' '_')"
if [ -z "${SPECAUDIT_E2E_CEILING:-}" ] && [ -f "$GUARD_FILE" ] && [ "$(cut -d' ' -f2 "$GUARD_FILE")" -gt "$(date +%s)" ]; then
  SPECAUDIT_E2E_CEILING="$(cut -d' ' -f1 "$GUARD_FILE")"
fi
if [ -z "${SPECAUDIT_E2E_CEILING:-}" ]; then
  GUARD_STREAM="$(mktemp "$GUARD_TMP/specaudit-usage-XXXX")"
  (cd "$GUARD_TMP" && claude -p "Reply with OK." --model haiku --output-format stream-json --verbose < /dev/null > "$GUARD_STREAM" 2>/dev/null)
  read -r SPECAUDIT_E2E_CEILING GUARD_RESET < <("$GUARD_PY" -c "
import json, subprocess, sys
u = json.loads(subprocess.run([sys.argv[1], sys.argv[2], sys.argv[3], '--pause-at', 'off'], capture_output=True, text=True).stdout)
if not (u['session'] and u['week']):
    sys.exit(1)
m = sys.argv[4]
margin = dict(p.split('=') for p in m.split(',')) if '=' in m else {'session': m, 'week': m}
pct = lambda w: min(100, round(u[w]['utilization'] * 100) + int(margin.get(w, 1)))
print(f\"session={pct('session')},week={pct('week')} {u['session']['resetsAt']}\")" "$GUARD_PY" "$GUARD_USAGE" "$GUARD_STREAM" "${SPECAUDIT_E2E_MARGIN:-1}")
  rm -f "$GUARD_STREAM"
  if [ -z "${SPECAUDIT_E2E_CEILING:-}" ]; then
    echo "usage ceiling: the account's usage could not be read; set SPECAUDIT_E2E_CEILING=\"session=N,week=N\"" >&2
    exit 3
  fi
  echo "$SPECAUDIT_E2E_CEILING $GUARD_RESET" > "$GUARD_FILE"
fi
export SPECAUDIT_E2E_CEILING
SPECAUDIT_E2E_PAUSE="--pause-at $SPECAUDIT_E2E_CEILING --no-auto-resume"
echo "usage ceiling: $SPECAUDIT_E2E_CEILING (%; past it, every audit of the tests pauses)"
