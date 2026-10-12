#!/usr/bin/env bash
# Two results folders, neither attested: with no argument, the command must not pick one.
. "$(dirname "$0")/../_fixtures/demo-repo.sh"
mkdir -p notes
echo "# Notes" > notes/design.md
for f in SpecAudit-20261010_210233 SpecAudit-20261009_163005; do mkdir -p "$f"; echo "# SpecAudit" > "$f/README.md"; done
cat > SPECAUDITS.md <<'MD'
# SpecAudit index

| Date | Audited object | Launched by | Result |
|---|---|---|---|
| [2026-10-10 21:02:33](#specaudit-20261010_210233) | `selection.md` | eval | FINISHED — Success |
| [2026-10-10 12:00:00](#specaudit-20261010_120000) | `selection.md` | eval | INTERRUPTED — suspended |
| [2026-10-09 16:30:05](#specaudit-20261009_163005) | `notes/ (folder, 1 document)` | eval | FINISHED — Partial, to continue |

## SpecAudit-20261010_210233

Audit of selection.md.

| | |
|---|---|
| Audited object | `selection.md` |
| Result | FINISHED — Success |
| Results folder | [SpecAudit-20261010_210233/](SpecAudit-20261010_210233/README.md) |
| Attested | no |

## SpecAudit-20261010_120000

Audit of selection.md.

| | |
|---|---|
| Audited object | `selection.md` |
| Result | INTERRUPTED — suspended |
| Results folder | none |
| Attested | — |

## SpecAudit-20261009_163005

Audit of notes/ (folder, 1 document).

| | |
|---|---|
| Audited object | `notes/ (folder, 1 document)` |
| Result | FINISHED — Partial, to continue |
| Results folder | [SpecAudit-20261009_163005/](SpecAudit-20261009_163005/README.md) |
| Attested | no |
MD
git -c user.name=eval -c user.email=eval@example.invalid add -A
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Audit results"
