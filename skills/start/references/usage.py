#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
"""Read the usage of the account an audit session runs on, from its stream, and request a pause above a threshold.

  python3 usage.py <stream.jsonl> [--pause-at session=75,week=50 | 80 | off] [--flag <pause-requested file>]

The audit session is launched with `--output-format stream-json --verbose`, whose stream carries, with every request,
a `rate_limit_event`: the utilization of the account's two windows, the session's five hours and the week, each with
the time it resets. Prints one JSON object:

  {"session": {"utilization": 0.16, "resetsAt": 1791800400}, "week": {...},
   "over": "session" | "week" | null,     a window at or above its threshold: the audit should pause
   "hit": "session" | "week" | null,      a window whose limit was reached: requests are refused until it resets
   "resumeAt": <epoch> | null, "resumeAtLocal": "YYYY-mm-dd HH:MM:SS" | null}

resumeAt is the reset of the window concerned, plus five minutes. With --flag, a window over its threshold or hit
writes the pause request (the window, its utilization and resumeAt, as JSON), unless one is already there: the
orchestrator checks that file before launching each agent. --pause-at defaults to 75 % of the session window and 50 % of the week; "off" requests
no pause, while a limit actually hit is still reported.
"""
import argparse
import json
import sys
import time
from pathlib import Path

WINDOWS = {"five_hour": "session", "seven_day": "week"}


def thresholds(spec):
    if spec == "off":
        return {}
    if "=" not in spec:
        return {"session": float(spec) / 100, "week": float(spec) / 100}
    out = {}
    for part in spec.split(","):
        name, value = part.split("=")
        if name.strip() not in ("session", "week"):
            raise ValueError(f"unknown window {name!r}: session or week")
        out[name.strip()] = float(value) / 100
    return out


def read(stream):
    state = {"session": None, "week": None, "hit": None, "hitReset": None}
    for line in Path(stream).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        info = event.get("rate_limit_info") if isinstance(event, dict) else None
        if not isinstance(info, dict):
            continue
        for key, name in WINDOWS.items():
            window = (info.get("unifiedWindows") or {}).get(key)
            if window:
                state[name] = {"utilization": window.get("utilization"), "resetsAt": window.get("resetsAt")}
        if info.get("status") == "rejected":
            state["hit"] = WINDOWS.get(info.get("rateLimitType"), "session")
            state["hitReset"] = info.get("resetsAt")
        elif info.get("status") == "allowed":
            state["hit"] = None
    return state


def decide(stream, pause_at="session=75,week=50", flag=None):
    """The usage of the stream, and the pause it calls for; writes the pause request to flag if one is due."""
    limits = thresholds(pause_at)
    s = read(stream) if Path(stream).exists() else {"session": None, "week": None, "hit": None, "hitReset": None}
    over = next((w for w in ("week", "session") if w in limits and s[w] and s[w]["utilization"] is not None
                 and s[w]["utilization"] >= limits[w]), None)
    concerned = s["hit"] or over
    reset = s["hitReset"] if s["hit"] else (s[over]["resetsAt"] if over else None)
    resume = reset + 300 if reset else None
    out = {"session": s["session"], "week": s["week"], "over": over, "hit": s["hit"], "resumeAt": resume,
           "resumeAtLocal": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(resume)) if resume else None}
    if concerned and flag and not Path(flag).exists():
        Path(flag).write_text(json.dumps({"window": concerned, "utilization": (s[concerned] or {}).get("utilization"),
                                          "resumeAt": resume, "resumeAtLocal": out["resumeAtLocal"]}) + "\n",
                              encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stream")
    ap.add_argument("--pause-at", default="session=75,week=50")
    ap.add_argument("--flag")
    a = ap.parse_args()
    try:
        print(json.dumps(decide(a.stream, a.pause_at, a.flag)))
    except ValueError as e:
        print(f"usage: --pause-at: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
