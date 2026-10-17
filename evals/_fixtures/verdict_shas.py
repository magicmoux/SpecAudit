#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
"""List the revisions an audit's register ties its agents and verdicts to.

  python3 verdict_shas.py <register.md>

Prints one abbreviated commit hash per line, without duplicates: the `Revision` cell of every row of the agent table,
and every hash of the errors' `Verdicts` lines (skills/start/references/register.md). Exit code 1, with the reason on
stderr, when an agent row has no revision, or when the register holds no `Verdicts` line at all: an audit that ran an
adjudicator must have recorded at least one verdict with its revision.
"""
import re
import sys
from pathlib import Path

SHA = re.compile(r"`([0-9a-f]{7,40})`")
BARE = re.compile(r"\b([0-9a-f]{7,40})\b")  # a Revision cell holds nothing else: backticks optional


def main(path):
    text = Path(path).read_text(encoding="utf-8")
    shas, problems = [], []
    agents = re.search(r"^## Agents\s*$(.*?)(?=^## )", text, re.M | re.S)
    if agents:
        lines = []  # the first table of the section: the chain digest may follow it
        for line in agents.group(1).splitlines():
            if line.startswith("|"):
                lines.append(line)
            elif lines:
                break
        header = [c.strip().lower() for c in lines[0].strip("|").split("|")] if lines else []
        col = header.index("revision") if "revision" in header else None
        for line in lines[2:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            found = BARE.findall(cells[col]) if col is not None and col < len(cells) else []
            if not found:
                problems.append(f"agent row without a revision: {cells[0] if cells else line}")
            shas += found
    else:
        problems.append("no agent table")
    # The field as register.md gives it ("- **Verdicts**: …"), or folded into another line of the entry ("Verdicts: …").
    verdicts = re.findall(r"\*{0,2}Verdicts\*{0,2}:(.*)$", text, re.M)
    if not verdicts:
        problems.append("no Verdicts line")
    for line in verdicts:
        found = SHA.findall(line)
        if not found:
            problems.append(f"Verdicts line without a revision: {line.strip()[:80]}")
        shas += found
    for s in dict.fromkeys(shas):
        print(s)
    for p in problems:
        print(p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
