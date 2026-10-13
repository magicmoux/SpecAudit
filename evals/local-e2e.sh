#!/usr/bin/env bash
# Local end-to-end test of a full audit of the demo, outside `claude plugin eval`, which refuses shell tools on platforms
# without a sandbox (Windows). It runs as you, in a throwaway repository under the temp directory.
# Usage: evals/local-e2e.sh [in-session|audit-session] [model] [audit options, default "--max-passes 1"]
# With "--auto --max-passes 2", the critical fix is applied and the fixed copy of the document is expected in the results folder.
set -uo pipefail
. "$(dirname "$0")/_fixtures/account-guard.sh"
. "$(dirname "$0")/_fixtures/consumption-check.sh"
MODE=${1:-in-session}
MODEL=${2:-sonnet}
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TEMP:-${TMPDIR:-/tmp}}"
# On Windows, $TEMP is C:\Users\...\Temp: normalize it to C:/..., the form the audit session records, and pick an
# interpreter that runs, since python3 may be the Microsoft Store stub there.
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
WORK="$(mktemp -d "$TMP/sa-e2e-XXXX")"
cd "$WORK" && . "$PLUGIN/evals/_fixtures/demo-repo.sh"

AUDIT_OPTS=${3:---max-passes 1}
OPTS="$AUDIT_OPTS --keep --model $MODEL"
[ "$MODE" = in-session ] && OPTS="$OPTS --in-session --no-worktree"
echo "plugin $PLUGIN, mode $MODE, model $MODEL, repo $WORK"
START=$(date +%s)  # the folder name must be a time between the launch and the end of the run
claude -p "/spec-audit:start selection.md $OPTS --account $ACCOUNT $SPECAUDIT_E2E_PAUSE" --plugin-dir "$PLUGIN" --model "$MODEL" --output-format json \
  --permission-mode dontAsk --allowedTools Read Write Edit Glob Grep Skill Agent Bash > result.json 2> stderr.log

AUDIT="$WORK"
[ "$MODE" = audit-session ] && AUDIT="$(dirname "$WORK")/$(basename "$WORK")-audit-selection"
DIR="$AUDIT/spec-audit/selection"
fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
check "register written" "[ -f '$DIR/register.md' ]"
check "inventory written" "[ -f '$DIR/inventory.md' ]"
check "report written" "[ -f '$DIR/report.md' ]"
check "lemma 3 fixed" "grep -qE '^\*\*Lemma 3\.\*\*.*(min\(k, ?\|L\|\)|min\(k, ?n\)|k ≤ \|L\||k ≤ n)' '$AUDIT/selection.md'"
check "proposition 4 unchanged" "grep -qF 'P_k(L ++ M) = P_k(P_k(L) ++ P_k(M))' '$AUDIT/selection.md'"
check "guard red first recorded" "grep -qiwE 'red' '$DIR/register.md'"
check "agent table filled" "grep -qE 'audit-selection-(reviewer|adjudicator)' '$DIR/register.md'"
# git log --grep rather than a pipe into grep -q: under pipefail, grep -q exits at the first match and git log's SIGPIPE fails the check.
check "internal revision committed" "[ -n \"\$(git -C '$AUDIT' log --oneline -F --grep 'incomplete: audit in progress')\" ]"
# The results folder comes back to the root of the original repository at closing (--keep applies "Keep the branch"),
# named by the launch time of the command, which this script takes just before launching.
RES="$(ls -d "$WORK"/SpecAudit-*/ 2>/dev/null | head -1)"
check "results folder named by launch time, to the second" "$PY -c \"import sys,re,datetime as d; m=re.search(r'/SpecAudit-(\\d{8}_\\d{6})(-\\d+)?/\\Z', sys.argv[1]); t=m and d.datetime.strptime(m.group(1), '%Y%m%d_%H%M%S').timestamp(); sys.exit(0 if m and $START - 1 <= t <= $START + 120 else 1)\" '$RES'"
# The index: a row of the summary table linked to the audit's section, FINISHED; the section links the results folder
# and starts with "Attested: no"; and the entry was committed at launch, before the audit's result.
NAME=$(basename "$RES")
check "index row for the audit, FINISHED" "grep -iE '^\\| \\[[^]]+\\]\\(#$NAME\\)' '$WORK/SPECAUDITS.md' | grep -F 'selection.md' | grep -q 'FINISHED'"
check "index section links the results folder" "awk -v id='## '\"$NAME\" '\$0==id{f=1;next} /^## /{f=0} f' '$WORK/SPECAUDITS.md' | grep -qF '[$NAME/]($NAME/README.md)'"
check "index entry committed at launch" "git -C '$WORK' log --reverse --format=%s -- SPECAUDITS.md | head -1 | grep -qi 'launched'"
WHO="$(git -C "$WORK" config user.name || id -un)"
check "index and README name who launched the audit" "grep -qF '$WHO' '$WORK/SPECAUDITS.md' && grep -qF '$WHO' '${RES}README.md'"
check "index section not attested at closing" "awk -v id='## '\"$NAME\" '\$0==id{f=1;next} /^## /{f=0} f' '$WORK/SPECAUDITS.md' | grep -qE '^\\| Attested \\| no \\|'"
check "README explains attestation" "grep -qi 'attest' '${RES}README.md' && grep -qF 'git tag -s' '${RES}README.md'"
check "results README with contents" "grep -q 'source/' '${RES}README.md' && grep -q 'resources/' '${RES}README.md'"
BASE="$(git -C "$WORK" rev-list --max-parents=0 HEAD | cut -c1-7)"  # the demo repository has a single starting commit
check "results README identifies the base commit" "grep -qF '$BASE' '${RES}README.md'"
# One agent at a time, each tied to a revision: the agents' journals show no overlap (audit session: its hooks write
# them), and every revision of the agent table and of the errors' Verdicts is a commit of the audit's branch.
STAMP="${NAME#SpecAudit-}"; BR="audit/$STAMP"; ON=HEAD
[ "$MODE" = audit-session ] && ON="$BR"
shas_on_branch() {
  local s
  "$PY" "$PLUGIN/evals/_fixtures/verdict_shas.py" "$DIR/register.md" | tr -d '\r' > "$WORK/shas.txt" || return 1
  [ -s "$WORK/shas.txt" ] || return 1
  while read -r s; do git -C "$AUDIT" merge-base --is-ancestor "$s" "$ON" 2>/dev/null || { echo "  $s is not a commit of $ON"; return 1; }; done < "$WORK/shas.txt"
}
check "every agent and every verdict tied to a commit of the audit's branch" "shas_on_branch"
if [ "$MODE" = audit-session ]; then
  check "no two agents overlapped (agent journals)" "$PY '$PLUGIN/evals/_fixtures/serial_check.py' '$AUDIT-scratch' > '$WORK/serial.log'"
  # The branch is the audit's identifier, audit/<stamp> with the results folder's stamp, and the only audit branch.
  check "audit branch named audit/<stamp>, the results folder's stamp" "git -C '$WORK' rev-parse -q --verify 'refs/heads/$BR' >/dev/null && [ \"\$(git -C '$WORK' branch --list 'audit/*' | wc -l)\" -eq 1 ]"
  check "register records the branch" "grep -qF '$BR' '$DIR/register.md'"
  FINAL="$(git -C "$WORK" rev-parse "$BR" 2>/dev/null)"
  # Never merged: no merge commit on the original branch, the final commit not in it, the document as it was, and the
  # original branch took only the results folder and the index, both committed there.
  check "audit branch ends with a final commit, nothing left uncommitted" "git -C '$AUDIT' log -1 --format=%s | grep -qi 'final' && [ -z \"\$(git -C '$AUDIT' status --porcelain --untracked-files=no)\" ]"
  check "nothing merged into the original branch" "[ -z \"\$(git -C '$WORK' log --merges --format=%h)\" ] && ! git -C '$WORK' merge-base --is-ancestor '$FINAL' HEAD"
  check "original document untouched" "cmp -s '$WORK/selection.md' '$PLUGIN/evals/_fixtures/selection.md'"
  ROOT_COMMIT="$(git -C "$WORK" rev-list --max-parents=0 HEAD)"
  check "original branch took only the results folder and the index" "[ -z \"\$(git -C '$WORK' log --format= --name-only '$ROOT_COMMIT..HEAD' | grep -v '^\$' | grep -vE '^(SPECAUDITS\\.md|$NAME/)')\" ]"
  check "results folder and index committed on the original branch" "git -C '$WORK' ls-files --error-unmatch '$NAME/README.md' >/dev/null 2>&1 && [ -z \"\$(git -C '$WORK' status --porcelain -- SPECAUDITS.md '$NAME')\" ]"
  check "results README names the branch and its final commit" "grep -qF '$BR' '${RES}README.md' && grep -qF '${FINAL:0:7}' '${RES}README.md'"
  check "index entry names the branch and its final commit" "awk -v id='## '\"$NAME\" '\$0==id{f=1;next} /^## /{f=0} f' '$WORK/SPECAUDITS.md' > '$WORK/entry.md' && grep -qF '$BR' '$WORK/entry.md' && grep -qF '${FINAL:0:7}' '$WORK/entry.md'"
fi
check "original source kept unfixed" "grep -qF '|P_k(L)| = k.' '${RES}source/selection.md'"
check "report and patch in results" "[ -f '${RES}report.md' ] && [ -f '${RES}resources/corrections.patch' ]"
check "executed counterexamples kept" "[ -n \"\$(find '${RES}resources/counterexamples' -name '*.py' 2>/dev/null)\" ]"
# The demo run stops after one iteration, usually with its critical fix pending, so the fixed copy may be absent; if it
# is there, it must be the fixed text, and if it is not, the README must say why.
if [ -f "${RES}selection.fixed.md" ]; then
  check "fixed copy at root is fixed" "grep -qE '^\*\*Lemma 3\.\*\*.*(min\(k, ?\|L\|\)|min\(k, ?n\)|k ≤ \|L\||k ≤ n)' '${RES}selection.fixed.md'"
else
  check "README explains the missing fixed copy" "grep -qiE 'pending|open|not (all )?fixed|corrections.patch' '${RES}README.md'"
fi
check "replay on the fixed document" "(cd '$RES' && $PY resources/replay.py --on fixed > '$WORK/replay-fixed.log')"
check "replay on the original shows the errors" "(cd '$RES' && $PY resources/replay.py --on source > '$WORK/replay-source.log')"
check "README documents the tests" "grep -qiE '^#+ *Tests' '${RES}README.md' && grep -qF -- '--on source' '${RES}README.md' && grep -qF 'replay.py' '${RES}README.md'"
check "no copy under the original name at root" "[ ! -e '${RES}selection.md' ]"
check "no runner cache in results" "[ -z \"\$(find '$RES' -name __pycache__ -o -name .pytest_cache)\" ]"
# A line that disclaims correctness ("this is not a claim that the document is correct") is the expected caution.
# The launch must work as the protocol writes it, not thanks to a launcher that works around it: no relaunch of the
# audit session recorded in the register, and no tool refused to the session or its agents.
[ "$MODE" = audit-session ] && check "launch files in the audit's own folder" "[ -f '$AUDIT-scratch/launch/protocol.md' ] && [ -f '$AUDIT-scratch/launch/agents.json' ]"
check "preflight passed at the first attempt" "grep -qiE 'Preflight: *passed[^|]*attempt 1\\b' '$DIR/register.md'"
# An agent relaunched by escalation is the protocol at work; only a relaunch of the audit session itself counts here.
check "audit session launched once" "! grep -qiE 'audit session[^|]*(relaunch|failed at start)|relaunch[^|]*audit session|allow list widened|audit session [2-9]' '$DIR/register.md'"
PROJ="$HOME/.claude/projects/$(echo "$AUDIT" | sed 's|[^A-Za-z0-9]|-|g')"
# A model may stray from the command forms now and then; the protocol's promise is that every refusal is caught,
# retried in an allowed form and recorded, so the register's count must match what the transcripts show.
check "register records the launcher's session id" "grep -qE '^- Session: .*[0-9a-f]{8}-[0-9a-f]{4}-' '$DIR/register.md' && ! grep -qF 'CLAUDE_SESSION_ID' '$DIR/register.md'"
check "every refusal recorded in the register" "[ \"\$($PY '$PLUGIN/evals/_fixtures/count_refusals.py' '$PROJ' 2>/dev/null | head -1 || echo 0)\" = \"\$(grep -oE '^- Refusals: *[0-9]+' '$DIR/register.md' | grep -oE '[0-9]+\$' || echo 0)\" ]"
# The report keeps the template's sections, in order, and ends with the summary of issues (references/report.md).
check "report sections in order, summary last" "$PY -c \"import re,sys; sys.exit(0 if re.search(r'## Result[\\s\\S]*## Cause graph[\\s\\S]*## Modified statements[\\s\\S]*## Errors[\\s\\S]*## Open points[\\s\\S]*## Corpus[\\s\\S]*## Scope of verification[\\s\\S]*## Consumption[\\s\\S]*## Branch and closing[\\s\\S]*## Summary of issues(?![\\s\\S]*\\n## )', open(sys.argv[1], encoding='utf-8').read()) else 1)\" '$DIR/report.md'"
# Consumption: measured by the launcher from the run's streams once the audit session ended, in place of the line the
# session wrote; with --in-session, the section says it was not measured. The index entry carries its total.
check "report has a Consumption section" "grep -q '^## Consumption' '$DIR/report.md'"
if [ "$MODE" = audit-session ]; then
  check "report's consumption total equals consumption.py on the run's streams" "consumption_matches '$DIR/report.md' '$AUDIT-scratch/launch'"
  check "index section has a Consumption row" "awk -v id='## '\"$NAME\" '\$0==id{f=1;next} /^## /{f=0} f' '$WORK/SPECAUDITS.md' | grep -qE '^\| Consumption \| [^|]*tokens'"
else
  check "report says consumption was not measured" "grep -A2 '^## Consumption' '$DIR/report.md' | grep -qi 'not measured'"
fi
check "report does not claim correctness" "[ -z \"\$(grep -iE '(document|it|proof)s? (is|are) (now )?(correct|verified)' '$DIR/report.md' | grep -viE '\\b(not|no|never|cannot)\\b')\" ]"
python -X utf8 -c "import json; d = json.load(open('result.json', encoding='utf-8')); print('cost USD', d.get('total_cost_usd'), '| turns', d.get('num_turns'), '| denials', len(d.get('permission_denials', [])))" 2>/dev/null
echo "wall-clock $(( $(date +%s) - START )) s"
# The audit session's own consumption, from its streams (the line above is the launcher's session only).
[ "$MODE" = audit-session ] && "$PY" "$PLUGIN/skills/start/references/consumption.py" "$AUDIT-scratch/launch" --no-transcripts --json 2>/dev/null \
  | "$PY" -X utf8 -c "import json,sys; d=json.load(sys.stdin); t=d['total']; print('audit session: tokens', t['total'], '(input', t['input'], '| cache write', t['cache_write'], '| cache read', t['cache_read'], '| output', str(t['output']) + ') | cost USD', d['cost']['total'])"
echo "$fails failure(s); artifacts in $WORK"
exit $((fails > 0))
