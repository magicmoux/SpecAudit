#!/usr/bin/env bash
# Regenerates examples/demo-result/: the results of two real audits of the demo, examples/demo/bubble-sort.md, so that
# a reader sees what an audit leaves without running one, and can replay its checks with Python alone.
#   partial/   --max-passes 1: the critical fix of the abstract and conclusion stays pending (partial, needs decision)
#   complete/  --auto --max-passes 2: every confirmed error fixed, with the fixed copy beside the original
# Each holds the project's index SPECAUDITS.md and the results folder, as files: no worktree, no git repository.
# Paths of the machine that ran it and session identifiers are replaced by placeholders (<repo>, <tmp>, <session>…).
# Nothing is written unless both runs pass the checks below: a failed or unexpected run is never frozen.
# Usage: evals/snapshot-demo.sh [model]
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
MODEL=${1:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
DOC=bubble-sort.md
STAGE="$(mktemp -d "$TMP/sa-snap-stage-XXXX")"
echo "plugin $PLUGIN, model $MODEL, staging $STAGE"

run() {  # <name> <options>: a throwaway repository with a neutral identity, then the audit
  local work
  work="$(mktemp -d "$TMP/sa-snap-$1-XXXX")"
  (cd "$work" && git init -q && git config user.name "SpecAudit demo" && git config user.email demo@example.invalid \
    && cp "$PLUGIN/examples/demo/$DOC" . && git add "$DOC" && git commit -qm "Demo specification" \
    && claude -p "/spec-audit:start $DOC $2 --keep --model $MODEL --account $ACCOUNT $SPECAUDIT_E2E_PAUSE" --plugin-dir "$PLUGIN" --model "$MODEL" \
      --output-format json --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash \
      > result.json 2> stderr.log)
  echo "$work" > "$STAGE/$1.work"
}
run partial "--max-passes 1" &
A=$!
run complete "--auto --max-passes 2" &
B=$!
wait $A; wait $B

fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
SECTIONS='## Result[\s\S]*## Cause graph[\s\S]*## Modified statements[\s\S]*## Errors[\s\S]*## Open points[\s\S]*## Corpus[\s\S]*## Scope of verification[\s\S]*## Consumption[\s\S]*## Branch and closing[\s\S]*## Summary of issues(?![\s\S]*\n## )'
for name in partial complete; do
  WORK="$(cat "$STAGE/$name.work")"; AUDIT="$WORK-audit-bubble-sort"; RES="$(ls -d "$WORK"/SpecAudit-*/ 2>/dev/null | head -1)"
  check "$name: results folder" "[ -n '$RES' ] && [ -f '${RES}report.md' ] && [ -f '${RES}resources/replay.py' ]"
  [ -n "$RES" ] || continue
  check "$name: report sections in order, summary last" "python3 -c \"import re,sys; sys.exit(0 if re.search(sys.argv[2], open(sys.argv[1], encoding='utf-8').read()) else 1)\" '${RES}report.md' '$SECTIONS'"
  check "$name: Lemma 3 fixed (the largest elements, at the end)" "grep -qiE '^\\*\\*Lemma 3\\.\\*\\*.*largest' '$AUDIT/$DOC'"
  check "$name: stability kept" "grep -qF '**Proposition 4.** A pass, and hence any sequence of passes' '$AUDIT/$DOC'"
  check "$name: index entry FINISHED" "grep -iE '^\\| \\[[^]]+\\]\\(#specaudit-' '$WORK/SPECAUDITS.md' | grep -q 'FINISHED'"
  check "$name: index section not attested at closing" "grep -qE '^\\| Attested \\| no \\|' '$WORK/SPECAUDITS.md'"
  if [ "$name" = partial ]; then
    check "partial: critical fix pending, no fixed copy" "[ ! -e '${RES}bubble-sort.fixed.md' ] && grep -qi 'needs decision' '$WORK/SPECAUDITS.md'"
  else
    check "complete: fixed copy beside the original" "[ -f '${RES}bubble-sort.fixed.md' ] && grep -qiE '^\\*\\*Lemma 3\\.\\*\\*.*largest' '${RES}bubble-sort.fixed.md'"
  fi

  # Copy the index and the results folder, without runner caches, then replace what names this machine or session.
  OUT="$STAGE/$name"; mkdir -p "$OUT"
  cp "$WORK/SPECAUDITS.md" "$OUT/" && cp -r "$RES" "$OUT/"
  find "$OUT" \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
  P="$(dirname "$WORK")"; N="$(basename "$WORK")"
  find "$OUT" -type f | while read -r f; do
    WORK="$WORK" P="$P" N="$N" PLUGIN="$PLUGIN" H="$HOME" python3 - "$f" <<'EOF'
import os, re, sys
path = sys.argv[1]
try:
    text = open(path, encoding="utf-8").read()
except UnicodeDecodeError:
    sys.exit(0)
e = os.environ
for old, new in ((e["WORK"], "<repo>"), (e["PLUGIN"], "<plugin>"), (e["P"] + "/", "<tmp>/"), (e["H"] + "/", "~/"),
                 (e["N"], "<repo>")):
    text = text.replace(old, new)
text = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "<session>", text)
text = re.sub(r"\bsession_[0-9A-Za-z]{20,}\b", "<session>", text)
open(path, "w", encoding="utf-8").write(text)
EOF
  done
  F="$(ls -d "$OUT"/SpecAudit-*/)"
  check "$name: nothing left that names this machine" "! grep -rqE '/tmp/|/home/|/root/|$N|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-' '$OUT'"
  # A partial result may leave form defects open behind its pending fix, so the lint can stay red on its fixed text.
  if [ "$name" = partial ]; then
    check "partial: replay from the snapshot, on the original" "(cd '$F' && python3 resources/replay.py --on source >/dev/null)"
  else
    check "complete: replay from the snapshot, on the original and on the fixed copy" "(cd '$F' && python3 resources/replay.py --on source >/dev/null && python3 resources/replay.py --on fixed >/dev/null)"
  fi
  find "$OUT" \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
  python3 -X utf8 -c "import json; d = json.load(open('$WORK/result.json', encoding='utf-8')); print('$name cost USD', round(d.get('total_cost_usd', 0), 2), '| turns', d.get('num_turns'))" 2>/dev/null | tee "$STAGE/$name.cost"
done

if [ "$fails" -gt 0 ]; then
  echo "$fails failure(s): examples/demo-result/ left unchanged; runs and staging kept in $TMP (sa-snap-*)"
  exit 1
fi

outcome() {  # the result and the count of errors, as the run's index states them
  local idx="$STAGE/$1/SPECAUDITS.md"
  echo "$(grep -m1 -E '^\| Result \|' "$idx" | cut -d'|' -f3 | sed 's/^ *//; s/ *$//'), $(grep -m1 -E '^\| Errors confirmed / fixed \|' "$idx" | cut -d'|' -f3 | sed 's/^ *//; s/ *$//') errors confirmed / fixed"
}
VERSION="$(python3 -c "import json; print(json.load(open('$PLUGIN/.claude-plugin/plugin.json'))['version'])")"
cat > "$STAGE/README.md" <<EOF
# Results of two audits of the demo

What \`/spec-audit:start\` left after auditing [\`../demo/bubble-sort.md\`](../demo/bubble-sort.md), copied as files: for each run, the project's index \`SPECAUDITS.md\` and the results folder \`SpecAudit-<stamp>/\` it links. They spoil the exercise: run the demo yourself first if you want to see what the audit finds on its own ([../README.md](../README.md)).

| Run | Options | Outcome |
|---|---|---|
| [partial/](partial/SPECAUDITS.md) | \`--max-passes 1 --keep\` | $(outcome partial); the fix of the abstract and the conclusion changes what the document claims, so it waits for a person: the fixes made are in \`resources/corrections.patch\` and \`resources/bubble-sort.partial.md\` |
| [complete/](complete/SPECAUDITS.md) | \`--auto --max-passes 2 --keep\` | $(outcome complete); critical fixes applied under \`--auto\`: \`bubble-sort.fixed.md\` beside \`source/bubble-sort.md\` |

Start with each folder's \`README.md\`, then \`report.md\`. The checks replay with Python alone, from a results folder: \`python3 resources/replay.py --on source\` shows each fixed error's guard red on the original, \`--on fixed\` every guard green on the complete run (on the partial one, the lint can stay red: form defects wait behind the pending fix).

Generated by \`evals/snapshot-demo.sh\` with spec-audit $VERSION, model $MODEL, on $(date -u +%Y-%m-%d). The runs used a throwaway repository and the git identity "SpecAudit demo"; paths of the machine that ran them are replaced by \`<repo>\` (the throwaway repository), \`<tmp>\` and \`~\`, and session identifiers by \`<session>\`. The worktree, the branch and the commits they name do not exist here. An audit is not deterministic: a new run finds the same planted errors, but may word them, order them or fix them differently. When the protocol changes, regenerate this folder rather than edit it.
EOF
rm -f "$STAGE"/*.work "$STAGE"/*.cost
rm -rf "$PLUGIN/examples/demo-result"
mv "$STAGE" "$PLUGIN/examples/demo-result"
echo "0 failure(s); examples/demo-result/ regenerated"
