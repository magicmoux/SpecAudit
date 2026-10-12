#!/usr/bin/env bash
# A project with one results folder in its index and no attestation tag.
. "$(dirname "$0")/../_fixtures/demo-repo.sh"
mkdir -p SpecAudit-20261010_210233
echo "# SpecAudit — selection.md" > SpecAudit-20261010_210233/README.md
cat > SPECAUDITS.md <<'MD'
# SpecAudit index

| Date | Audited object | Launched by | Result |
|---|---|---|---|
| [2026-10-10 21:02:33](#specaudit-20261010_210233) | `selection.md` | eval | FINISHED — Success |

## SpecAudit-20261010_210233

Audit of selection.md.

| | |
|---|---|
| Audited object | `selection.md` |
| Result | FINISHED — Success |
| Results folder | [SpecAudit-20261010_210233/](SpecAudit-20261010_210233/README.md) |
| Attested | no |
MD
git -c user.name=eval -c user.email=eval@example.invalid add -A
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Audit results"
