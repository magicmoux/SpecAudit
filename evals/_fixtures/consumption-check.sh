# Sourced by the local end-to-end scripts, after $PY and $PLUGIN are set.
# consumption_matches <report.md> <launch folder>: the total of the report's "## Consumption" section (its Total row)
# equals the one consumption.py measures on the run's streams. The total does not depend on the transcripts, so they
# are not read.
consumption_matches() {
  local in_report measured
  in_report=$("$PY" -c "
import re, sys
t = open(sys.argv[1], encoding='utf-8').read()
s = re.search(r'^## Consumption\n(.*?)(?=^## |\Z)', t, re.M | re.S)
m = s and re.search(r'^\| \*\*Total\*\* \|(?:[^|]*\|){6} *([\d,]+) *\|', s.group(1), re.M)
print(m.group(1).replace(',', '') if m else '')" "$1")
  measured=$("$PY" "$PLUGIN/skills/start/references/consumption.py" "$2" --no-transcripts --json \
    | "$PY" -c "import json, sys; print(json.load(sys.stdin)['total']['total'])")
  echo "  consumption: report $in_report, measured $measured"
  [ -n "$in_report" ] && [ "$in_report" = "$measured" ]
}
