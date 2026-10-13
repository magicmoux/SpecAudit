#!/usr/bin/env bash
# Turns the current directory, a copy of _fixtures/arch-project/, into a git repository: a project with an original
# manuscript and hard-to-find references (source/), its revised version and proofs (artifacts/), and a Lean
# development with a correspondence table (mechanization/). Lean need not be installed: init only reads it.
# Usage: cp -r _fixtures/arch-project/. <dir> && cd <dir> && bash _fixtures/arch-repo.sh [--no-arch]
#   without --no-arch, the architecture /spec-audit:init is expected to propose is written and committed too.
set -euo pipefail
FIX="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
G() { git -c user.name=eval -c user.email=eval@example.invalid -c core.autocrlf=false "$@"; }
git init -q
G add -A
G commit -qm "Selection paper, its revision and its mechanization"
if [ "${1:-}" != --no-arch ]; then
  PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
  "$PY" "$FIX/../../skills/init/scan.py" > SPECAUDIT_ARCH.md
  G add SPECAUDIT_ARCH.md
  G commit -qm "Architecture"
fi
