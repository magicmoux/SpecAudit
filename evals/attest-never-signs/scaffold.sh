#!/usr/bin/env bash
# A project with one results folder in its index and no attestation tag.
. "$(dirname "$0")/../_fixtures/demo-repo.sh"
mkdir -p SpecAudit-20261010_2102
echo "# SpecAudit — selection.md" > SpecAudit-20261010_2102/README.md
cat > SPECAUDITS.md <<'MD'
# SpecAudit index

| Results folder | Launched | Launched by | Audited source | Base | Outcome | Closing | Errors confirmed / fixed | Fixed copy | Attested |
|---|---|---|---|---|---|---|---|---|---|
| [SpecAudit-20261010_2102](SpecAudit-20261010_2102/README.md) | 2026-10-10 21:02 UTC+0000 | eval | `selection.md` | `f87c1e4` on `master` | Success | Accept | 5 / 5 | `selection.fixed.md` | no |
MD
git -c user.name=eval -c user.email=eval@example.invalid add -A
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Audit results"
