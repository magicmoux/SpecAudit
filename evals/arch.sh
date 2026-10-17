#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
# Test of the architecture scripts, without a model: skills/init/scan.py proposes SPECAUDIT_ARCH.md for the fixture
# project _fixtures/arch-project/ (manuscript, revised copy, references, Lean development with a correspondence table)
# and for the demo; skills/start/references/arch.py refuses an audit without the file, and refuses any change outside
# what the audit may change, at commit time (check) and in the audit session (hook). Usage: evals/arch.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIX="$ROOT/evals/_fixtures"
SCAN="$ROOT/skills/init/scan.py"
ARCH="$ROOT/skills/start/references/arch.py"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
TMP="$(mktemp -d "${TEMP:-${TMPDIR:-/tmp}}/sa-arch-XXXX")"
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
G() { git -c user.name=eval -c user.email=eval@example.invalid -c core.autocrlf=false "$@"; }

fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
# role <json> <path>: the role the proposal gives to exactly that path entry
role() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8')); print(next((e['role'] + '/' + str(e['profile']) for e in d['paths'] if e['path'] == [sys.argv[2]]), 'absent'))" "$1" "$2"; }
j() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8')); print($2)" "$1"; }

# --- The fixture project: init's proposal --------------------------------------------------------------------------
P="$TMP/project"; mkdir -p "$P" && cp -r "$FIX/arch-project/." "$P/"
(cd "$P" && bash "$FIX/arch-repo.sh" --no-arch >/dev/null)
"$PY" "$SCAN" --root "$P" --json > "$TMP/proposal.json" || { echo "FAIL scan.py ran"; exit 1; }
O="$TMP/proposal.json"
check "artifacts/ audited, formal" "[ \"\$(role $O artifacts/)\" = audited/formal ]"
check "source/manuscript.md original" "[ \"\$(role $O source/manuscript.md)\" = original/None ]"
check "source/references/ sources" "[ \"\$(role $O source/references/)\" = sources/None ]"
check "mechanization/ oracle" "[ \"\$(role $O mechanization/)\" = oracle/None ]"
check "README.md not listed (read-only)" "[ \"\$(role $O README.md)\" = absent ]"
check "no other path entry" "[ \"\$(j $O 'len(d[\"paths\"])')\" = 4 ]"
check "Lean oracle: kind, command run from the root" "[ \"\$(j $O '(d[\"oracles\"][0][\"kind\"], d[\"oracles\"][0][\"command\"])')\" = \"('formal', 'lake -d mechanization build')\" ]"
check "Lean oracle: correspondence table found" "[ \"\$(j $O 'd[\"oracles\"][0][\"correspondence\"]')\" = \"['mechanization/CORRESPONDENCE.md']\" ]"
check "Lean oracle: guards where the lakefile builds them" "[ \"\$(j $O 'd[\"oracles\"][0][\"guards\"]')\" = \"['mechanization/Guards/']\" ]"
check "mapped pair: revised paper and the Lean library" "[ \"\$(j $O '(d[\"pairs\"][0][\"document\"], sorted(d[\"pairs\"][0][\"counterpart\"]))')\" = \"(['artifacts/manuscript-revised.md'], ['mechanization/Selection.lean', 'mechanization/Selection/'])\" ]"
check "description taken from the project's README" "j $O 'd[\"paths\"][0][\"description\"]' | grep -q 'revised version'"
"$PY" "$SCAN" --root "$P" > "$TMP/SPECAUDIT_ARCH.md"
check "the proposal renders as the documented tables" "grep -qF '| \`artifacts/\` | audited | formal |' '$TMP/SPECAUDIT_ARCH.md' && grep -qF '| \`mechanization/\` | formal | \`lake -d mechanization build\` | \`mechanization/CORRESPONDENCE.md\` | \`mechanization/Guards/\` |' '$TMP/SPECAUDIT_ARCH.md'"
check "init writes nothing" "[ ! -e '$P/SPECAUDIT_ARCH.md' ] && [ -z \"\$(git -C '$P' status --porcelain)\" ]"

# --- The demo: a single document ------------------------------------------------------------------------------------
D="$TMP/demo"; mkdir -p "$D" && (cd "$D" && . "$FIX/demo-repo.sh" && G rm -q SPECAUDIT_ARCH.md && G commit -qm "No architecture")
"$PY" "$SCAN" --root "$D" --json > "$TMP/demo.json"
check "demo: selection.md audited, formal, alone" "[ \"\$(role $TMP/demo.json selection.md)\" = audited/formal ] && [ \"\$(j $TMP/demo.json 'len(d[\"paths\"])')\" = 1 ]"

# --- start refuses without the file ---------------------------------------------------------------------------------
"$PY" "$ARCH" require --root "$D" > "$TMP/req.out" 2> "$TMP/req.err"; rc=$?
check "require: exit 2 without SPECAUDIT_ARCH.md" "[ $rc -eq 2 ]"
check "require: says to run /spec-audit:init" "grep -qF '/spec-audit:init' '$TMP/req.err'"
cp "$TMP/SPECAUDIT_ARCH.md" "$P/" && (cd "$P" && G add SPECAUDIT_ARCH.md && G commit -qm "Architecture")
check "require: passes on init's proposal" "'$PY' '$ARCH' require --root '$P' >/dev/null"
mkdir -p "$TMP/bad" && printf '# SpecAudit architecture

## Paths

| Path | Role | Profile | Description |
|---|---|---|---|
| `x.md` | fixed | formal | — |
' > "$TMP/bad/SPECAUDIT_ARCH.md"
"$PY" "$ARCH" require --root "$TMP/bad" >/dev/null 2>&1; rc=$?
check "require: exit 1 on an unknown role, with nothing audited" "[ $rc -eq 1 ]"

# --- check: what an internal revision may commit --------------------------------------------------------------------
c() { "$PY" "$ARCH" check --root "$P" --corpus spec-guards "$@" >/dev/null 2>&1; }
check "check: a fix of the audited paper" "c artifacts/manuscript-revised.md"
check "check: a guard in the corpus, the register, the index" "c spec-guards/test_F_1_1_text.py spec-audit/x/register.md SPECAUDITS.md"
check "check: a guard module where the oracle says" "c mechanization/Guards/F_1_1.lean"
check "check: refuses the original manuscript" "! c source/manuscript.md"
check "check: refuses a reference" "! c source/references/references.bib"
check "check: refuses the oracle's build file" "! c mechanization/lakefile.toml"
check "check: refuses a path the file does not list" "! c README.md"
check "check: refuses the architecture itself and the configuration" "! c SPECAUDIT_ARCH.md && ! c .specaudit.md"
check "check: refuses a mapped counterpart changed alone" "! c mechanization/Selection/Lemmas.lean"
check "check: accepts it with its document" "c mechanization/Selection/Lemmas.lean mechanization/CORRESPONDENCE.md artifacts/manuscript-revised.md"
echo "x" >> "$P/source/manuscript.md" && echo "y" >> "$P/artifacts/manuscript-revised.md" && G -C "$P" add source/manuscript.md artifacts/manuscript-revised.md
"$PY" "$ARCH" check --root "$P" --staged > "$TMP/staged.out" 2>&1; rc=$?
check "check --staged: refuses the staged change of the original, names it and its role" "[ $rc -eq 1 ] && grep -qF 'refused: source/manuscript.md (original)' '$TMP/staged.out' && ! grep -q 'refused: artifacts' '$TMP/staged.out'"
G -C "$P" reset -q --hard

# --- hook: the audit session refuses at the tool call ---------------------------------------------------------------
h() {  # h <tool> <path> [agent]: exit code of the hook on that call
  local agent=""; [ -n "${3:-}" ] && agent=',"agent_id":"a1"'
  printf '{"hook_event_name":"PreToolUse","tool_name":"%s","tool_input":{"file_path":"%s"},"cwd":"%s"%s}' "$1" "$2" "$P" "$agent" \
    | "$PY" "$ARCH" hook --root "$P" --corpus spec-guards >/dev/null 2>&1; echo $?
}
check "hook: the orchestrator edits the audited paper" "[ \$(h Edit '$P/artifacts/manuscript-revised.md') = 0 ]"
check "hook: refuses the orchestrator an edit of a reference" "[ \$(h Edit '$P/source/references/references.bib') = 2 ]"
check "hook: refuses the orchestrator a write in the original" "[ \$(h Write source/manuscript.md) = 2 ]"
check "hook: lets the orchestrator edit a counterpart (the commit checks the pair)" "[ \$(h Edit '$P/mechanization/Selection/Lemmas.lean') = 0 ]"
check "hook: an agent may read the architecture and the paper" "[ \$(h Read '$P/SPECAUDIT_ARCH.md' agent) = 0 ] && [ \$(h Read '$P/artifacts/manuscript-revised.md' agent) = 0 ]"
check "hook: refuses an agent the index, results folders, records, configuration" "[ \$(h Read '$P/SPECAUDITS.md' agent) = 2 ] && [ \$(h Read '$P/SpecAudit-20260901_100000/report.md' agent) = 2 ] && [ \$(h Read '$P/spec-audit/selection/register.md' agent) = 2 ] && [ \$(h Read '$P/.specaudit.md' agent) = 2 ]"
check "hook: refuses an agent the original manuscript" "[ \$(h Read '$P/source/manuscript.md' agent) = 2 ]"
check "hook: refuses an agent any write in the project, not in its scratch directory" "[ \$(h Write '$P/artifacts/x.md' agent) = 2 ] && [ \$(h Write '$TMP/scratch/t.py' agent) = 0 ]"
check "hook: the orchestrator reads the index" "[ \$(h Read '$P/SPECAUDITS.md') = 0 ]"
check "hook: ignores other tools and malformed events" "[ \"\$(echo '{\"tool_name\":\"Bash\"}' | '$PY' '$ARCH' hook --root '$P'; echo \$?)\" = 0 ] && [ \"\$(echo 'not json' | '$PY' '$ARCH' hook --root '$P'; echo \$?)\" = 0 ]"

# --- the orchestrator's configuration: deprecated keys still read for one version -----------------------------------
printf -- '---\nnormative:\n  "artifacts/*.md": [docs/notation.md]\n---\nNotes.\n' > "$P/.specaudit.md"
check "normative: a deprecated key of the configuration still counts" "'$PY' '$ARCH' normative --root '$P' --config '$P/.specaudit.md' artifacts/manuscript-revised.md | grep -qx 'docs/notation.md'"
check "show: warns that the keys are deprecated" "'$PY' '$ARCH' show --root '$P' --config '$P/.specaudit.md' | grep -qi 'deprecated'"
rm "$P/.specaudit.md"

# --- init run again: the changes against the existing file ----------------------------------------------------------
sed -i 's/| `source\/references\/` | sources |/| `source\/references\/` | normative |/' "$P/SPECAUDIT_ARCH.md"
check "diff: a role changed by hand is shown against the proposal" "'$PY' '$SCAN' --root '$P' --diff | grep -qF '~ path source/references/: normative → sources'"

echo "$fails failure(s)"
exit $((fails > 0))
