#!/usr/bin/env bash
# Test of skills/start/references/account.py check, on simulated accounts: configuration folders under a throwaway home,
# each with a fake-auth.json standing for what `claude auth status` would say there. An audit stays on the account that
# launched it: the check passes only while the recorded folder is logged in to the recorded e-mail, and names the other
# folders logged in to it. No model, no network, no real login read. Usage: evals/account.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REFS="$ROOT/skills/start/references"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
TMP="$(mktemp -d "${TEMP:-${TMPDIR:-/tmp}}/sa-account-XXXX")"
command -v cygpath >/dev/null 2>&1 && { TMP="$(cygpath -m "$TMP")"; REFS="$(cygpath -m "$REFS")"; }
HOME_DIR="$TMP/home"
mkdir -p "$HOME_DIR/.claude" "$HOME_DIR/.claude-perso" "$HOME_DIR/.claude-other"
auth() { printf '{"loggedIn": %s, "email": %s}\n' "$2" "$3" > "$HOME_DIR/$1/fake-auth.json"; }

# run <expected exit> <args...>: account.py's main with `claude auth status` replaced by the folder's fake-auth.json,
# and the home moved to the throwaway one. Prints the output; the exit code goes to $TMP/rc.
run() {
  "$PY" -I -c "
import json, os, sys
from pathlib import Path
os.environ['HOME'] = os.environ['USERPROFILE'] = sys.argv[1]
os.environ.pop('CLAUDE_CONFIG_DIR', None)
os.environ.pop('CLAUDE_CODE_USER_EMAIL', None)
os.environ.update(json.loads(sys.argv[2]))
sys.path.insert(0, sys.argv[3])
import account
def status(config):
    f = Path(os.path.expanduser(str(config))) / 'fake-auth.json'
    return json.loads(f.read_text()) if f.exists() else {'loggedIn': False}
account.status = status
sys.argv = ['account.py'] + sys.argv[4:]
sys.exit(account.main())
" "$HOME_DIR" "$1" "$REFS" "${@:2}"
  echo $? > "$TMP/rc"
}
rc() { cat "$TMP/rc"; }

fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }

auth .claude true '"launcher@example.com"'
auth .claude-perso true '"other@example.com"'
auth .claude-other false null
D="$HOME_DIR/.claude"

out="$(run '{}' check "$D" launcher@example.com)"
check "same folder, same account: passes, says nothing" "[ \"\$(rc)\" = 0 ] && [ -z \"\$out\" ]"
out="$(run '{}' check "$D" LAUNCHER@Example.com)"
check "the e-mail compared without case" "[ \"\$(rc)\" = 0 ]"

# The folder logged in to another account while the audit waited (claude auth login in the same folder).
auth .claude true '"newcomer@example.com"'
out="$(run '{}' check "$D" launcher@example.com)"
check "another account in the folder: refused" "[ \"\$(rc)\" = 1 ]"
check "  names the account expected and the one found" "echo \"\$out\" | grep -q '\"expected\": \"launcher@example.com\"' && echo \"\$out\" | grep -q '\"found\": \"newcomer@example.com\"'"
check "  nowhere else logged in to it" "echo \"\$out\" | grep -q '\"elsewhere\": \[\]'"

# The launcher's account logged in to another folder: the same account, a folder the launch may switch to.
auth .claude-other true '"launcher@example.com"'
out="$(run '{}' check "$D" launcher@example.com)"
check "the account in another folder: refused here, that folder named" "[ \"\$(rc)\" = 1 ] && echo \"\$out\" | grep -q '\.claude-other\"\]'"

auth .claude false null
out="$(run '{}' check "$D" launcher@example.com)"
check "the folder logged out: refused" "[ \"\$(rc)\" = 1 ] && echo \"\$out\" | grep -q '\"loggedIn\": false'"
rm "$D/fake-auth.json"
out="$(run '{}' check "$HOME_DIR/.claude-gone" launcher@example.com)"
check "a folder that no longer exists: refused" "[ \"\$(rc)\" = 1 ]"

# The desktop app's credentials do not decide: check reads the folder, whatever the session's account.
auth .claude true '"launcher@example.com"'
out="$(run '{"CLAUDE_CODE_USER_EMAIL": "newcomer@example.com", "CLAUDE_CODE_ACCOUNT_UUID": "x"}' check "$D" launcher@example.com)"
check "the session's own account ignored for an audit session" "[ \"\$(rc)\" = 0 ]"

# --in-session: the account is the session's.
out="$(run '{"CLAUDE_CODE_USER_EMAIL": "launcher@example.com"}' check --session launcher@example.com)"
check "in-session, same account: passes" "[ \"\$(rc)\" = 0 ]"
out="$(run '{"CLAUDE_CODE_USER_EMAIL": "newcomer@example.com"}' check --session launcher@example.com)"
check "in-session, another account: refused" "[ \"\$(rc)\" = 1 ] && echo \"\$out\" | grep -q newcomer@example.com"
out="$(run '{}' check --session launcher@example.com)"
check "in-session, account unknown: exit 3" "[ \"\$(rc)\" = 3 ]"

# The real script, without the fake: its usage names check.
usage="$("$PY" "$REFS/account.py" 2>&1)"
check "usage names check" "echo \"\$usage\" | grep -q 'account.py check <dir> <email>'"

echo "$fails failure(s); files in $TMP"
exit $((fails > 0))
