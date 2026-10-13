#!/usr/bin/env python3
"""Check from the agents' journals that no two agents of an audit ran at the same time.

  python3 serial_check.py <scratch root>

Every agent's scratch directory under the root holds the journal.jsonl that the audit session's hooks write
(skills/start/references/journal.py): a "launch" record when the orchestrator launches it, and a "stop" record when it
ends. Each launch opens an interval, closed by the next stop of the same journal (a replacement relaunched in the same
directory opens a new one); a launch never closed is an agent killed or cut, which runs to the end of the audit for
this check. Prints one line per agent and every overlap; exit code 0 when the intervals are disjoint, 1 otherwise, 2 when
no agent was found.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

FAR = datetime.max


def intervals(root):
    found = []
    for journal in sorted(Path(root).rglob("journal.jsonl")):
        start = None
        for line in journal.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                t = datetime.strptime(r["t"], "%Y-%m-%dT%H:%M:%S")
            except (ValueError, KeyError):
                continue
            if r.get("event") == "launch":
                if start is not None:  # relaunched without a stop: the previous one is counted as running until now
                    found.append((start, t, journal.parent))
                start = t
            elif r.get("event") == "stop" and start is not None:
                found.append((start, t, journal.parent))
                start = None
        if start is not None:
            found.append((start, FAR, journal.parent))
    return sorted(found, key=lambda i: (i[0], i[1]))


def main(root):
    agents = intervals(root)
    if not agents:
        print(f"no agent journal under {root}")
        return 2
    overlaps = 0
    end, holder = None, None
    for start, stop, scratch in agents:
        name = Path(scratch).relative_to(root).as_posix()
        print(f"{start:%H:%M:%S} – {'running' if stop is FAR else f'{stop:%H:%M:%S}'}  {name}")
        if end is not None and start < end:
            print(f"  OVERLAP: {name} launched while {holder} was still running")
            overlaps += 1
        if end is None or stop > end:
            end, holder = stop, name
    print(f"{len(agents)} agent run(s), {overlaps} overlap(s)")
    return 1 if overlaps else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
