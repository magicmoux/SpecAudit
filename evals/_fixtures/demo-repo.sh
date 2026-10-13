#!/usr/bin/env bash
# Seeds the eval workspace with a git repository holding the demo specification and its architecture.
# Usage from a case's scaffold script: . "$(dirname "$0")/../_fixtures/demo-repo.sh"
set -euo pipefail
FIX="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$FIX/selection.md" .
bash "$FIX/write-arch.sh" selection.md > SPECAUDIT_ARCH.md
git init -q
git -c user.name=eval -c user.email=eval@example.invalid add selection.md SPECAUDIT_ARCH.md
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Demo specification"
