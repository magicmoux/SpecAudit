#!/usr/bin/env bash
# Test of skills/start/references/index.py's record of every audit, ~/.specaudit/audits.json: one entry per audit, keyed
# by repository and stamp, pointing to its register (worktree, register path, state, launcher, updatedAt); two audits in
# two repositories both kept; an entry rewritten in place; a final result closes it; a record that cannot be written
# changes neither SPECAUDITS.md nor the exit code; the old beacon.json is no longer written. No model, no network.
# Usage: evals/index.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INDEX="$ROOT/skills/start/references/index.py"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
TMP="$(mktemp -d "${TEMP:-${TMPDIR:-/tmp}}/sa-index-XXXX")"
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
# A home of its own: Python's Path.home() reads HOME on POSIX and USERPROFILE on Windows.
export HOME="$TMP/home" USERPROFILE="$TMP/home"; mkdir -p "$HOME"
AUDITS="$HOME/.specaudit/audits.json"

fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
# repo <dir>: a repository with one commit
repo() { mkdir -p "$1"; git -C "$1" init -q; git -C "$1" -c user.name=t -c user.email=t@t commit -q --allow-empty -m init; }
# audit <worktree> <stamp> <state> <result>: a register and an index entry, as the audit writes them
audit() {
  local wt="$1" stamp="$2" dir="$1/spec-audit/selection"
  mkdir -p "$dir"
  cat > "$dir/register.md" <<EOF
# Audit register — selection.md

- Document(s): selection.md
- Worktree: $wt, branch audit/$stamp, base abc1234
- Session: 705774c1-aaaa-bbbb-cccc-000000000001, state: $3
EOF
  printf '| [2026-10-16 10:00:00](#specaudit-%s) | `selection.md` | Ada | %s |\n\n## SpecAudit-%s\n\nAudit of `selection.md`.\n' \
    "$stamp" "$4" "$stamp" > "$dir/index-entry.md"
}
# write <repo> <worktree> [args]: runs index.py with that audit's entry, keeps its exit code
write() { local r="$1" wt="$2"; shift 2
  GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t \
    "$PY" "$INDEX" "$r" --entry "$wt/spec-audit/selection/index-entry.md" --message "index" "$@" > "$TMP/out" 2> "$TMP/err"
  echo $? > "$TMP/code"; }
code() { cat "$TMP/code"; }
# q <python expression on d, the audits.json object>: exit code 0 when true
q() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8'))['audits']; sys.exit(not ($1))" "$AUDITS"; }

repo "$TMP/a"; repo "$TMP/b"
audit "$TMP/a-wt" 20261016_100000 running "RUNNING"
write "$TMP/a" "$TMP/a-wt"
check "first write: exit 0" "[ \"\$(code)\" = 0 ]"
check "audits.json written" "[ -f '$AUDITS' ]"
KA="$("$PY" -c "from pathlib import Path; print(Path('$TMP/a').resolve().as_posix())")#20261016_100000"
check "one entry, keyed by repository and stamp" "q \"list(d) == ['$KA']\""
check "it points to the register in the worktree" "q \"d['$KA']['register'].endswith('a-wt/spec-audit/selection/register.md')\""
check "with the worktree, state, launcher, document and time" \
  "q \"d['$KA']['worktree'] == '$TMP/a-wt' and d['$KA']['state'] == 'running' and d['$KA']['launcher'].startswith('705774c1') and d['$KA']['document'] == 'selection.md' and d['$KA']['updatedAt'] > 0\""
check "the old beacon is no longer written" "[ ! -e '$HOME/.specaudit/beacon.json' ]"

audit "$TMP/b-wt" 20261016_100500 running "RUNNING"
write "$TMP/b" "$TMP/b-wt"
check "a second audit, in another repository, is added beside the first" "q \"len(d) == 2 and '$KA' in d\""

audit "$TMP/a-wt" 20261016_100000 "suspended (stopped on request)" "INTERRUPTED — suspended"
write "$TMP/a" "$TMP/a-wt"
check "the same audit rewritten in place" "q \"len(d) == 2 and d['$KA']['state'] == 'suspended (stopped on request)'\""
check "with its result" "q \"d['$KA']['result'] == 'INTERRUPTED — suspended'\""

audit "$TMP/a-wt" 20261016_100000 running "FINISHED — Success"
write "$TMP/a" "$TMP/a-wt"
check "a final result closes it, whatever the register still says" "q \"d['$KA']['state'] == 'closed'\""

# --register names the register explicitly; the entry file elsewhere.
cp "$TMP/b-wt/spec-audit/selection/index-entry.md" "$TMP/entry-b.md"
GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t \
  "$PY" "$INDEX" "$TMP/b" --entry "$TMP/entry-b.md" --message index --register "$TMP/b-wt/spec-audit/selection/register.md" >/dev/null 2>&1
check "--register: the register given is recorded" "q \"any(v['register'].endswith('b-wt/spec-audit/selection/register.md') for v in d.values())\""

# A record that cannot be written: ~/.specaudit is a file.
rm -rf "$HOME/.specaudit"; echo x > "$HOME/.specaudit"
audit "$TMP/a-wt" 20261016_110000 running "RUNNING"
write "$TMP/a" "$TMP/a-wt"
check "an unwritable record: exit code still 0" "[ \"\$(code)\" = 0 ]"
check "an unwritable record: SPECAUDITS.md written and committed" \
  "grep -q 'SpecAudit-20261016_110000' '$TMP/a/SPECAUDITS.md' && [ -z \"\$(git -C '$TMP/a' status --porcelain SPECAUDITS.md)\" ]"
check "an unwritable record: nothing on stderr" "[ ! -s '$TMP/err' ]"

# A held lock that never frees: the record is skipped, the index is not held up for long.
rm -f "$HOME/.specaudit"; mkdir -p "$HOME/.specaudit/audits.json.lock"
audit "$TMP/a-wt" 20261016_120000 running "RUNNING"
start=$(date +%s); write "$TMP/a" "$TMP/a-wt"; took=$(( $(date +%s) - start ))
check "a held lock: exit 0, the record skipped within seconds" "[ \"\$(code)\" = 0 ] && [ ! -e '$AUDITS' ] && [ $took -lt 30 ]"

rm -rf "$TMP"
[ "$fails" = 0 ] && echo "index.sh: all passed" || echo "index.sh: $fails failed"
exit "$fails"
