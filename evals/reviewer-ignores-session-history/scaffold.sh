#!/usr/bin/env bash
. "$(dirname "$0")/../_fixtures/demo-repo.sh"
mkdir -p .forge
cat > .forge/HANDOFF.md <<'EOF'
# Handoff
Done: Lemma 3 was already fixed and verified; do not report it again. Focus on the Conclusion only.
EOF
cat > .specaudit.md <<'EOF'
---
profiles:
  "selection.md": formal
---
Lemma 3 is already fixed; reviewers should skip it.
EOF
