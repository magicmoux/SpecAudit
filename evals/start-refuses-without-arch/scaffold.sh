#!/usr/bin/env bash
# The demo without its architecture: the audit must not run on a guessed structure.
. "$(dirname "$0")/../_fixtures/demo-repo.sh"
git -c user.name=eval -c user.email=eval@example.invalid rm -q SPECAUDIT_ARCH.md
git -c user.name=eval -c user.email=eval@example.invalid commit -qm "No architecture"
