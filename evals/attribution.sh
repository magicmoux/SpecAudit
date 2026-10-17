#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
# Test of the credit check, .github/scripts/attribution.py, on a throwaway repository: a contributor credited in a code
# file's header or in a REUSE.toml entry passes, one missing from either fails and is named, the last matching entry
# applies, a Co-authored-by person counts, an AI tool and an Assisted-by trailer do not, .mailmap merges identities, and
# LICENSE and deleted files are not checked. No model, no network. Usage: evals/attribution.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECK="$ROOT/.github/scripts/attribution.py"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
TMP="$(mktemp -d "${TEMP:-${TMPDIR:-/tmp}}/sa-attribution-XXXX")"
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
R="$TMP/repo"; mkdir -p "$R" && cd "$R" || exit 2

fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
G() { git -c commit.gpgsign=false -c tag.gpgsign=false -c user.name="${AN:-Owner}" -c user.email="${AE:-owner@example.org}" "$@"; }
run() { "$PY" "$CHECK" base > "$TMP/out" 2>&1; echo $? > "$TMP/code"; }
code() { cat "$TMP/code"; }
reset() { G checkout -q -B pr base; }

git init -q -b main . && G config core.autocrlf false
printf '# SPDX-FileCopyrightText: 2026 Owner\n# SPDX-License-Identifier: X\nprint(1)\n' > a.py
printf '# Doc\n' > doc.md
printf '# License\n' > LICENSE
cat > REUSE.toml <<'EOF'
version = 1
[[annotations]]
path = "**.md"
SPDX-FileCopyrightText = "2026 Owner"
SPDX-License-Identifier = "X"
EOF
G add -A && G commit -qm base && G tag base

reset; echo 'print(2)' >> a.py; AN=Jane AE=jane@example.org G commit -qam "Jane edits a.py"
run
check "uncredited header: fails" "[ \"\$(code)\" = 1 ] && grep -q 'a.py: Jane' '$TMP/out'"
sed -i '1a # SPDX-FileCopyrightText: 2026 Jane <jane@example.org>' a.py; AN=Jane AE=jane@example.org G commit -qam "Credit Jane"
run
check "credited in the header: passes" "[ \"\$(code)\" = 0 ]"

reset; echo more >> doc.md; AN=Jane AE=jane@example.org G commit -qam "Jane edits doc.md"
run
check "uncredited REUSE.toml file: fails" "[ \"\$(code)\" = 1 ] && grep -q 'doc.md: Jane' '$TMP/out'"
printf '[[annotations]]\npath = "doc.md"\nSPDX-FileCopyrightText = ["2026 Owner", "2026 Jane"]\nSPDX-License-Identifier = "X"\n' >> REUSE.toml
AN=Jane AE=jane@example.org G commit -qam "Credit Jane in REUSE.toml"
run
check "credited by the last matching entry: passes" "[ \"\$(code)\" = 0 ]"
printf '[[annotations]]\npath = "*.md"\nSPDX-FileCopyrightText = "2026 Owner"\nSPDX-License-Identifier = "X"\n' >> REUSE.toml
G commit -qam "A later entry for every .md"
run
check "a later entry without her: fails" "[ \"\$(code)\" = 1 ] && grep -q 'doc.md: Jane' '$TMP/out'"

reset; echo 'print(3)' >> a.py
G commit -qam "Owner edits a.py" -m "$(printf 'Co-authored-by: Ann <ann@example.org>\nAssisted-by: Some Tool <tool@example.org>')"
run
check "Co-authored-by counts, Assisted-by does not" "[ \"\$(code)\" = 1 ] && grep -q 'a.py: Ann\$' '$TMP/out'"

reset; echo 'print(4)' >> a.py
G commit -qam "Owner edits a.py" -m "Co-authored-by: Claude <noreply@anthropic.com>"
run
check "an AI co-author is not a person" "[ \"\$(code)\" = 0 ]"

reset; echo 'print(5)' >> a.py; AN="O. Old" AE=old@example.org G commit -qam "Owner under an old address"
run
check "unmapped identity: fails" "[ \"\$(code)\" = 1 ] && grep -q 'O. Old' '$TMP/out'"
echo 'Owner <owner@example.org> O. Old <old@example.org>' > .mailmap
run
check ".mailmap merges identities: passes" "[ \"\$(code)\" = 0 ]"
rm .mailmap

reset; echo more >> LICENSE; printf 'x\n' > gone.py; AN=Jane AE=jane@example.org G add -A
AN=Jane AE=jane@example.org G commit -qm "Jane edits LICENSE, adds gone.py"; G rm -q gone.py && G commit -qm "Remove gone.py"
run
check "LICENSE and deleted files are not checked" "[ \"\$(code)\" = 0 ]"

echo "$fails failure(s)"
exit $((fails > 0))
