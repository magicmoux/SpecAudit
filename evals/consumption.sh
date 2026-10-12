#!/usr/bin/env bash
# Test of skills/start/references/consumption.py on synthetic streams: a first run (orchestrator and two agents, one
# assistant message repeated on two lines, two result events whose modelUsage is cumulative) and a resumed run during
# which the session window resets. No model, no network. Usage: evals/consumption.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONSUMPTION="$ROOT/skills/start/references/consumption.py"
FIX="$ROOT/evals/_fixtures"
PY=python3; "$PY" -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1 || PY=python
TMP="$(mktemp -d "${TEMP:-${TMPDIR:-/tmp}}/sa-consumption-XXXX")"
command -v cygpath >/dev/null 2>&1 && TMP="$(cygpath -m "$TMP")"
# A launch folder after one --resume: the first run moved aside as stream-1.jsonl, the last one as stream.jsonl.
mkdir -p "$TMP/launch" && cp "$FIX/stream-sample.jsonl" "$TMP/launch/stream-1.jsonl" && cp "$FIX/stream-sample-resume.jsonl" "$TMP/launch/stream.jsonl"
# The agents' transcripts, where Claude Code keeps them: their exact output (the stream's is counted at the start of
# streaming). The reviewer's has one message on two lines, to be counted once.
SUB="$TMP/config/projects/C--w-demo-audit-demo/s-one/subagents" && mkdir -p "$SUB"
a() { printf '{"type":"assistant","message":{"id":"%s","usage":{"output_tokens":%s}}}\n' "$1" "$2"; }
{ a ma1 150; a ma1 150; a ma2 300; } > "$SUB/agent-aaa.jsonl"
a mb1 70 > "$SUB/agent-bbb.jsonl"

fails=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fails=$((fails + 1)); fi; }
# j <json file> <python expression on d>: prints the value
j() { "$PY" -c "import json,sys; d=json.load(open(sys.argv[1], encoding='utf-8')); print($2)" "$1"; }

"$PY" "$CONSUMPTION" "$TMP/launch" --no-transcripts --json > "$TMP/plain.json" || { echo "FAIL consumption.py ran"; exit 1; }
"$PY" "$CONSUMPTION" "$TMP/launch" --config-dir "$TMP/config" --json > "$TMP/exact.json"
"$PY" "$CONSUMPTION" "$FIX/stream-sample.jsonl" --no-transcripts --json > "$TMP/one.json"
P="$TMP/plain.json"; E="$TMP/exact.json"; O="$TMP/one.json"

check "both runs read, in order" "[ \"\$(j $P \"[s.rsplit('/', 1)[-1] for s in d['streams']]\")\" = \"['stream-1.jsonl', 'stream.jsonl']\" ]"
check "rows: orchestrator, then the agents in launch order" "[ \"\$(j $P \"[r['name'] for r in d['rows']]\")\" = \"['orchestrator', 'reviewer-a', 'adjudicator-F-1-1']\" ]"
check "roles and models from the launch" "[ \"\$(j $P \"[(r['role'], r['model']) for r in d['rows'][1:]]\")\" = \"[('reviewer, iter-1', 'claude-sonnet-5-5'), ('adjudicator, iter-1', 'claude-haiku-5-5')]\" ]"
# The orchestrator: its messages of both runs; its output, the sum of its result events (300 + 150 + 50).
check "orchestrator summed over both runs" "[ \"\$(j $P \"[d['rows'][0][k] for k in ('input', 'cache_write', 'cache_read', 'output')]\")\" = '[26, 1400, 19000, 500]' ]"
# The reviewer's first message is on two lines: counted twice, its cache write would be 4500.
check "repeated message counted once" "[ \"\$(j $P \"[d['rows'][1][k] for k in ('input', 'cache_write', 'cache_read')]\")\" = '[10, 2500, 7000]' ]"
# The total is the last result's modelUsage of each run (the first result's is not added to it), summed over runs.
check "total from the last result of each run" "[ \"\$(j $P \"[d['total'][k] for k in ('input', 'cache_write', 'cache_read', 'output', 'total')]\")\" = '[39, 4900, 28000, 1020, 33959]' ]"
check "without transcripts, the agents' output is not attributed" "[ \"\$(j $P \"(d['rows'][1]['output_exact'], d['unattributed']['output'], d['unattributed']['input'])\")\" = '(False, 520, 0)' ]"
check "shares sum to 100" "[ \"\$(j $P \"round(sum(r['share'] for r in d['rows'] + [d['unattributed']]))\")\" = 100 ]"
check "orchestrator's share" "[ \"\$(j $P \"d['rows'][0]['share']\")\" = 61.6 ]"
check "with transcripts, each agent's exact output" "[ \"\$(j $E \"([r['output'] for r in d['rows']], d['unattributed'], d['output_from_transcripts'])\")\" = '([500, 450, 70], None, True)' ]"
check "with transcripts, rows sum to the total" "[ \"\$(j $E \"sum(r['total'] for r in d['rows']) == d['total']['total']\")\" = True ]"
check "cost per model and in total, from the last results" "[ \"\$(j $P \"(d['cost']['total'], sorted(d['cost']['models'].items()))\")\" = \"(0.87, [('claude-haiku-5-5', 0.05), ('claude-sonnet-5-5', 0.82)])\" ]"
check "no cost per agent" "[ \"\$(j $P \"any('cost' in r for r in d['rows'])\")\" = False ]"
# Windows: run 1, session 10 % to 15 %, week 20 % to 21 %; run 2, the session window resets, the week goes 30 % to 31 %.
check "one run: shares of both windows" "[ \"\$(j $O \"(d['windows']['session']['share'], d['windows']['week']['share'])\")\" = '(5.0, 1.0)' ]"
check "a reset during a run: no share, and why" "[ \"\$(j $P \"(d['windows']['session']['share'], d['windows']['session']['runs'][1]['share'], 'reset' in d['windows']['session']['reason'])\")\" = '(None, None, True)' ]"
check "week summed over the runs" "[ \"\$(j $P \"d['windows']['week']['share']\")\" = 2.0 ]"
check "index cell" "[ \"\$(j $P \"d['index']\")\" = '34.0 k tokens, \$0.87, 2 points of the week window' ]"

# The Markdown section, and its place in the report.
"$PY" "$CONSUMPTION" "$TMP/launch" --no-transcripts > "$TMP/section.md"
check "section: heading, total row, caveats" "grep -q '^## Consumption' '$TMP/section.md' && grep -qF '| **Total** | | | 39 | 4,900 | 28,000 | 1,020 | 33,959 | 100 % |' '$TMP/section.md' && grep -qi 'share of tokens is not the share of cost' '$TMP/section.md' && grep -qi 'other activity on the same account' '$TMP/section.md' && grep -qi 'no cost per agent' '$TMP/section.md'"
check "section: the reset said, not a number" "grep -qE '^\\| Session \\(5 h\\) \\| 2 \\| 90 % \\| 2 % \\| the window reset during the run' '$TMP/section.md'"
printf '# Precision audit — demo.md\n\n## Scope of verification\nChecked.\n\n## Consumption\nMeasured by the launcher once the session ends.\n\n## Branch and closing\nKept.\n' > "$TMP/report.md"
"$PY" "$CONSUMPTION" "$TMP/launch" --no-transcripts --report "$TMP/report.md" > /dev/null
check "report: placeholder replaced in place" "! grep -q 'once the session ends' '$TMP/report.md' && [ \"\$(grep -c '^## Consumption' '$TMP/report.md')\" = 1 ] && \"$PY\" -c \"import re,sys; sys.exit(0 if re.search(r'## Scope of verification[\\s\\S]*## Consumption[\\s\\S]*33,959[\\s\\S]*## Branch and closing\\nKept', open(sys.argv[1], encoding='utf-8').read()) else 1)\" '$TMP/report.md'"
printf '# Precision audit\n\n## Scope of verification\nChecked.\n\n## Branch and closing\nKept.\n' > "$TMP/report2.md"
"$PY" "$CONSUMPTION" "$TMP/launch" --no-transcripts --report "$TMP/report2.md" > /dev/null
check "report: section inserted before Branch and closing when missing" "\"$PY\" -c \"import re,sys; sys.exit(0 if re.search(r'Checked\\.\\n\\n## Consumption[\\s\\S]*## Branch and closing', open(sys.argv[1], encoding='utf-8').read()) else 1)\" '$TMP/report2.md'"
check "no stream: says so" "\"$PY\" '$CONSUMPTION' '$TMP/none' --no-transcripts | grep -q 'Not measured'"

echo "$fails failure(s); files in $TMP"
exit $((fails > 0))
