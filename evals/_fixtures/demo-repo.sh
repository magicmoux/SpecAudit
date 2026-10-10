#!/usr/bin/env bash
# Seeds the eval workspace with a git repository holding the demo specification.
# Usage from a case's scaffold script: . "$(dirname "$0")/../_fixtures/demo-repo.sh" [extra files to copy from _fixtures]
set -euo pipefail
FIX="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$FIX/selection.md" .
git init -q
git -c user.name=eval -c user.email=eval@example.invalid add selection.md
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "Demo specification"
