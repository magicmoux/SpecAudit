#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
# Test of skills/attest/verify.py on real signed tags: a throwaway repository under the temp directory, a throwaway SSH
# key, one results folder per status. Needs git and ssh-keygen; no network, no model. Usage: evals/attest-verify.sh
set -uo pipefail
VERIFY="$(cd "$(dirname "$0")/.." && pwd)/skills/attest/verify.py"
# python3 may be the Microsoft Store stub on Windows: take python when python3 does not run Python 3.
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
TMP="$(mktemp -d "${TEMP:-${TMPDIR:-/tmp}}/sa-attest-XXXX")"
cd "$TMP" || exit 2
ssh-keygen -q -t ed25519 -N "" -f key -C signer </dev/null >/dev/null || exit 2
ssh-keygen -q -t ed25519 -N "" -f other -C other </dev/null >/dev/null || exit 2
echo "signer@example.invalid $(cat key.pub)" > allowed

mkdir repo && cd repo && git init -q
# Some environments replace git's SSH signing program with their own signer; the test needs the standard one.
git config gpg.ssh.program ssh-keygen
# A global tag.gpgsign or commit.gpgsign would sign the lightweight tag below, or ask it for a message: only `tag -s` signs.
git config tag.gpgsign false && git config commit.gpgsign false
git config user.name "Test Signer" && git config user.email signer@example.invalid
git config gpg.format ssh && git config user.signingkey "$TMP/key" && git config gpg.ssh.allowedSignersFile "$TMP/allowed"
printf '# SpecAudit index\n\n| Date | Audited object | Launched by | Result |\n|---|---|---|---|\n' > SPECAUDITS.md
for f in 0600 0500 0400 0300 0200 0100; do
  echo "| [2026-10-10 ${f:0:2}:${f:2:2}](#specaudit-20261010_${f}00) | \`a.md\` | x | FINISHED — Success |" >> SPECAUDITS.md
done
echo "| [2026-10-10 00:30](#specaudit-20261010_003000) | \`a.md\` | x | INTERRUPTED — suspended |" >> SPECAUDITS.md
for f in 0600 0500 0400 0300 0200 0100; do
  d="SpecAudit-20261010_${f}00"; mkdir "$d"; echo "report" > "$d/README.md"
  printf '\n## %s\n\nAudit of a.md.\n\n| | |\n|---|---|\n| Audited object | `a.md` |\n| Result | FINISHED — Success |\n| Results folder | [%s/](%s/README.md) |\n| Attested | no |\n' "$d" "$d" "$d" >> SPECAUDITS.md
done
# An interrupted audit: an entry, but no results folder, hence nothing to attest.
printf '\n## SpecAudit-20261010_003000\n\nAudit of a.md, stopped.\n\n| | |\n|---|---|\n| Audited object | `a.md` |\n| Result | INTERRUPTED — suspended |\n| Results folder | none yet |\n| Attested | — |\n' >> SPECAUDITS.md
git add -A && git commit -qm "audits"

git tag -s specaudit/SpecAudit-20261010_010000 -m attest                       # valid, unchanged
git tag specaudit/SpecAudit-20261010_020000                                    # lightweight: no signature
git tag -s specaudit/SpecAudit-20261010_030000 -m attest                       # valid, then the folder changes
git -c user.signingkey="$TMP/other" tag -s specaudit/SpecAudit-20261010_040000 -m attest   # key not trusted here
git tag -s specaudit/SpecAudit-20261010_050000 -m attest                       # valid, then the tag is tampered with
tampered=$(git cat-file tag specaudit/SpecAudit-20261010_050000 | sed 's/^attest$/attest, tampered/' | git hash-object -t tag -w --stdin)
git update-ref refs/tags/specaudit/SpecAudit-20261010_050000 "$tampered"
echo "changed" >> SpecAudit-20261010_030000/README.md && git commit -qam "change after attestation"
# SpecAudit-20261010_060000: no tag

out="$($PY "$VERIFY")"; rc=$?
fails=0
expect() { if grep -qE "^$1  $2" <<<"$out"; then echo "PASS $1 $2"; else echo "FAIL $1: expected '$2'"; fails=$((fails + 1)); fi; }
expect SpecAudit-20261010_010000 "yes: signer@example.invalid, [0-9-]+$"
expect SpecAudit-20261010_020000 "unsigned tag$"
expect SpecAudit-20261010_030000 "changed since attestation$"
expect SpecAudit-20261010_040000 "signed, not verified here$"
expect SpecAudit-20261010_050000 "invalid signature$"
expect SpecAudit-20261010_060000 "no$"
if [ "$rc" -eq 1 ]; then echo "PASS exit code 1 (not every folder attested)"; else echo "FAIL exit code $rc, expected 1"; fails=$((fails + 1)); fi

# Targets: a stamp, a path, an audited source (the newest folder of that source), an unknown target (an error, never
# an approximation), and the folders still to attest.
check_out() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1: got '$3', expected '$2'"; fails=$((fails + 1)); fi; }
check_out "target by stamp" "SpecAudit-20261010_010000  yes" "$($PY "$VERIFY" 20261010_010000 | cut -c1-30)"
check_out "target by path" "SpecAudit-20261010_030000  changed since attestation" "$($PY "$VERIFY" ./SpecAudit-20261010_030000/)"
check_out "target by source, newest" "SpecAudit-20261010_060000  no" "$($PY "$VERIFY" a.md 2>/dev/null)"
$PY "$VERIFY" SpecAudit-20991231_000000 >/dev/null 2>&1; check_out "unknown target is an error" "2" "$?"
check_out "pending folders" "SpecAudit-20261010_060000 SpecAudit-20261010_050000 SpecAudit-20261010_040000 SpecAudit-20261010_030000 SpecAudit-20261010_020000" "$($PY "$VERIFY" --pending | tr -d '\r' | tr '\n' ' ' | sed 's/ $//')"

$PY "$VERIFY" --update >/dev/null
att() { awk -v id="## $1" '$0==id{f=1;next} /^## /{f=0} f && /^\| Attested \|/' SPECAUDITS.md; }
if att SpecAudit-20261010_010000 | grep -qE '^\| Attested \| yes: signer@example.invalid, [0-9-]+ \|$' \
   && att SpecAudit-20261010_060000 | grep -qE '^\| Attested \| no \|$' \
   && att SpecAudit-20261010_003000 | grep -qE '^\| Attested \| — \|$' \
   && grep -qF '| INTERRUPTED — suspended |' SPECAUDITS.md; then
  echo "PASS --update writes each section's Attested cell only"
else
  echo "FAIL --update"; fails=$((fails + 1))
fi
check_out "an audit without results folder is not listed" "" "$($PY "$VERIFY" | grep -F 'SpecAudit-20261010_003000')"
echo "$fails failure(s); artifacts in $TMP"
exit $((fails > 0))
