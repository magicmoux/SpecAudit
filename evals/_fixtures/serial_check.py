#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
"""Check that no two agents of an audit ran at the same time.

  python3 serial_check.py <scratch root> [<stream.jsonl>...]

Two independent records, both kept outside the orchestrator's control:
  - the audit session's streams (default: every stream*.jsonl of <scratch root>/launch): the orchestrator's Agent calls,
    each a tool_use answered by its tool_result. A foreground agent's result arrives when it ends, so between a launch
    and its result there must be no other launch;
  - the agents' journals, which the session's hooks write (skills/start/references/journal.py): a "launch" record
    opens an interval, closed by the next "stop" record of the same journal, or else by the time of the result.md or
    partial.md the hook wrote (a stop record can be missing when a reply was empty); a launch never closed runs to the
    end of the audit for this check.
Prints each agent and every overlap; exit code 0 when both records show agents one at a time, 1 otherwise, 2 when
neither found an agent.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

FAR = datetime.max


def stream_overlaps(paths):
    """(launches, overlaps) from the orchestrator's Agent calls in the streams."""
    launches, overlaps = 0, []
    for path in paths:
        open_call = None
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("parent_tool_use_id") is not None:
                continue
            message = e.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict):
                    continue
                if e.get("type") == "assistant" and b.get("type") == "tool_use" and b.get("name") in ("Agent", "Task"):
                    launches += 1
                    desc = (b.get("input") or {}).get("description") or b.get("id")
                    if open_call:
                        overlaps.append(f"stream: {desc} launched before {open_call[1]} returned")
                    open_call = (b.get("id"), desc)
                elif e.get("type") == "user" and b.get("type") == "tool_result" and open_call \
                        and b.get("tool_use_id") == open_call[0]:
                    open_call = None
    return launches, overlaps


def ended_at(scratch):
    times = [datetime.fromtimestamp(os.path.getmtime(scratch / f)).replace(microsecond=0)
             for f in ("result.md", "partial.md") if (scratch / f).exists()]
    return max(times) if times else FAR


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
                if start is not None:  # relaunched without a stop record: the previous one ended before this launch
                    found.append((start, t, journal.parent))
                start = t
            elif r.get("event") == "stop" and start is not None:
                found.append((start, t, journal.parent))
                start = None
        if start is not None:
            end = ended_at(journal.parent)
            found.append((start, end if end >= start else FAR, journal.parent))
    return sorted(found, key=lambda i: (i[0], i[1]))


def main(root, streams):
    root = Path(root)
    streams = streams or sorted((root / "launch").glob("stream*.jsonl"))
    launches, problems = stream_overlaps(streams)
    agents = intervals(root)
    if not agents and not launches:
        print(f"no agent found under {root}")
        return 2
    end, holder = None, None
    for start, stop, scratch in agents:
        name = Path(scratch).relative_to(root).as_posix()
        print(f"{start:%H:%M:%S} - {'running' if stop is FAR else f'{stop:%H:%M:%S}'}  {name}")
        if end is not None and start < end:
            problems.append(f"journal: {name} launched while {holder} was still running")
        if end is None or stop > end:
            end, holder = stop, name
    for p in problems:
        print("  OVERLAP " + p)
    print(f"{launches} launch(es) in the stream, {len(agents)} agent run(s) in the journals, {len(problems)} overlap(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2:]))
