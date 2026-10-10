#!/usr/bin/env bash
# Two results folders, neither attested: with no argument, the command must not pick one.
. "$(dirname "$0")/../_fixtures/demo-repo.sh"
mkdir -p notes
echo "# Notes" > notes/design.md
for f in SpecAudit-20261010_2102 SpecAudit-20261009_1630; do mkdir -p "$f"; echo "# SpecAudit" > "$f/README.md"; done
cat > SPECAUDITS.md <<'MD'
# SpecAudit index

| Results folder | Launched | Launched by | Audited source | Base | Outcome | Closing | Errors confirmed / fixed | Fixed copy | Attested |
|---|---|---|---|---|---|---|---|---|---|
| [SpecAudit-20261010_2102](SpecAudit-20261010_2102/README.md) | 2026-10-10 21:02 UTC+0000 | eval | `selection.md` | `f87c1e4` on `master` | Success | Accept | 5 / 5 | `selection.fixed.md` | no |
| [SpecAudit-20261009_1630](SpecAudit-20261009_1630/README.md) | 2026-10-09 16:30 UTC+0000 | eval | `notes/` (folder, 1 document) | `f87c1e4` on `master` | Partial, to continue | Keep | 1 / 1 | no | no |
MD
git -c user.name=eval -c user.email=eval@example.invalid add -A
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Audit results"
