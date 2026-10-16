"""Prints the audits index.py records, one JSON object, or nothing when there is none:

  {"audits": [{"repo": "C:/Repos/demo", "stamp": "20261015_223658", "register": "C:/Repos/demo-wt/spec-audit/x/register.md",
               "worktree": "...", "state": "running", "launcher": "705774c1-...", "updatedAt": 1792096470, ...}, ...]}

From ~/.specaudit/audits.json, the index of every audit (index.py writes it at each write of an index), and from the
single-audit beacon of earlier versions, ~/.specaudit/beacon.json, for an audit indexed by an older index.py: that one
names only a repository and a stamp, with no register. The mod has no way to name the home folder itself, so this
script reads the files for it.
"""
import json
from pathlib import Path

home = Path.home() / ".specaudit"
out = []
try:
    data = json.loads((home / "audits.json").read_text(encoding="utf-8"))
    out = [v for v in data["audits"].values() if isinstance(v, dict) and v.get("repo")]
except (OSError, ValueError, KeyError, TypeError, AttributeError):
    pass
try:
    beacon = json.loads((home / "beacon.json").read_text(encoding="utf-8"))
    stamp = str(beacon.get("id", "")).removeprefix("SpecAudit-")
    if beacon.get("repo") and not any(a["repo"].lower() == beacon["repo"].lower() and a.get("stamp") == stamp for a in out):
        out.append({"repo": beacon["repo"], "stamp": stamp or None, "updatedAt": beacon.get("at")})
except (OSError, ValueError, AttributeError):
    pass
if out:
    print(json.dumps({"audits": out}))
