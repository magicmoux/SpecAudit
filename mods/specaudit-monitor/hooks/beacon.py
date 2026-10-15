"""Prints the beacon index.py leaves at each write of an index, ~/.specaudit/beacon.json, or nothing without one:

  {"repo": "C:/Users/me/AppData/Local/Temp/sa-e2e-n0GV", "id": "SpecAudit-20261015_223658", "at": 1792096470}

The mod has no way to name the home folder itself, so this script reads the file for it.
"""
import json
from pathlib import Path

try:
    print(json.dumps(json.loads((Path.home() / ".specaudit" / "beacon.json").read_text(encoding="utf-8"))))
except (OSError, ValueError):
    pass
