#!/usr/bin/env bash
# Test of skills/attest/verify.py on real signed tags: a throwaway repository under the temp directory, a throwaway SSH
# key, one results folder per status. Needs git and ssh-keygen; no network, no model. Usage: evals/attest-verify.sh
set -uo pipefail
VERIFY="$(cd "$(dirname "$0")/.." && pwd)/skills/attest/verify.py"
TMP="$(mktemp -d "${TEMP:-${TMPDIR:-/tmp}}/sa-attest-XXXX")"
cd "$TMP" || exit 2
ssh-keygen -q -t ed25519 -N "" -f key -C signer </dev/null >/dev/null || exit 2
ssh-keygen -q -t ed25519 -N "" -f other -C other </dev/null >/dev/null || exit 2
echo "signer@example.invalid $(cat key.pub)" > allowed

mkdir repo && cd repo && git init -q
# Some environments replace git's SSH signing program with their own signer; the test needs the standard one.
git config gpg.ssh.program ssh-keygen
git config user.name "Test Signer" && git config user.email signer@example.invalid
git config gpg.format ssh && git config user.signingkey "$TMP/key" && git config gpg.ssh.allowedSignersFile "$TMP/allowed"
printf '# SpecAudit index\n\n| Results folder | Launched | Launched by | Audited source | Base | Outcome | Closing | Errors confirmed / fixed | Fixed copy | Attested |\n|---|---|---|---|---|---|---|---|---|---|\n' > SPECAUDITS.md
for f in 0600 0500 0400 0300 0200 0100; do
  d="SpecAudit-20261010_$f"; mkdir "$d"; echo "report" > "$d/README.md"
  echo "| [$d]($d/README.md) | x | x | \`a.md\` | x | x | x | x | no | no |" >> SPECAUDITS.md
done
git add -A && git commit -qm "audits"

git tag -s specaudit/SpecAudit-20261010_0100 -m attest                       # valid, unchanged
git tag specaudit/SpecAudit-20261010_0200                                    # lightweight: no signature
git tag -s specaudit/SpecAudit-20261010_0300 -m attest                       # valid, then the folder changes
git -c user.signingkey="$TMP/other" tag -s specaudit/SpecAudit-20261010_0400 -m attest   # key not trusted here
git tag -s specaudit/SpecAudit-20261010_0500 -m attest                       # valid, then the tag is tampered with
tampered=$(git cat-file tag specaudit/SpecAudit-20261010_0500 | sed 's/^attest$/attest, tampered/' | git hash-object -t tag -w --stdin)
git update-ref refs/tags/specaudit/SpecAudit-20261010_0500 "$tampered"
echo "changed" >> SpecAudit-20261010_0300/README.md && git commit -qam "change after attestation"
# SpecAudit-20261010_0600: no tag

out="$(python3 "$VERIFY")"; rc=$?
fails=0
expect() { if grep -qE "^$1  $2" <<<"$out"; then echo "PASS $1 $2"; else echo "FAIL $1: expected '$2'"; fails=$((fails + 1)); fi; }
expect SpecAudit-20261010_0100 "yes: signer@example.invalid, [0-9-]+$"
expect SpecAudit-20261010_0200 "unsigned tag$"
expect SpecAudit-20261010_0300 "changed since attestation$"
expect SpecAudit-20261010_0400 "signed, not verified here$"
expect SpecAudit-20261010_0500 "invalid signature$"
expect SpecAudit-20261010_0600 "no$"
if [ "$rc" -eq 1 ]; then echo "PASS exit code 1 (not every folder attested)"; else echo "FAIL exit code $rc, expected 1"; fails=$((fails + 1)); fi

# Targets: a stamp, a path, an audited source (the newest folder of that source), an unknown target (an error, never
# an approximation), and the folders still to attest.
check_out() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1: got '$3', expected '$2'"; fails=$((fails + 1)); fi; }
check_out "target by stamp" "SpecAudit-20261010_0100  yes" "$(python3 "$VERIFY" 20261010_0100 | cut -c1-28)"
check_out "target by path" "SpecAudit-20261010_0300  changed since attestation" "$(python3 "$VERIFY" ./SpecAudit-20261010_0300/)"
check_out "target by source, newest" "SpecAudit-20261010_0600  no" "$(python3 "$VERIFY" a.md 2>/dev/null)"
python3 "$VERIFY" SpecAudit-20991231_0000 >/dev/null 2>&1; check_out "unknown target is an error" "2" "$?"
check_out "pending folders" "SpecAudit-20261010_0600 SpecAudit-20261010_0500 SpecAudit-20261010_0400 SpecAudit-20261010_0300 SpecAudit-20261010_0200" "$(python3 "$VERIFY" --pending | tr '\n' ' ' | sed 's/ $//')"

python3 "$VERIFY" --update >/dev/null
if grep -qE '^\| \[SpecAudit-20261010_0100\].*\| yes: signer@example.invalid, [0-9-]+ \|$' SPECAUDITS.md \
   && grep -qE '^\| \[SpecAudit-20261010_0600\].*\| no \| no \|$' SPECAUDITS.md; then
  echo "PASS --update writes the Attested column only"
else
  echo "FAIL --update"; fails=$((fails + 1))
fi
echo "$fails failure(s); artifacts in $TMP"
exit $((fails > 0))
