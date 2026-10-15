"""Reads an audit's launch folder (stream-<n>.jsonl, then stream.jsonl) and prints one JSON object:

  {"session": {"start": 0.21, "now": 0.24, "resetsAt": 1792087800} | null, "week": {...} | null,
   "turns": <orchestrator turns>, "tokens": <tokens, each message counted once>, "cost": <USD of the finished runs>}

usage.py's reading of the rate-limit events, done line by line so that a long audit's stream is never loaded whole.
"""
import json
import re
import sys
from pathlib import Path

WINDOWS = {"five_hour": "session", "seven_day": "week"}


def main(folder):
    folder = Path(folder)
    numbered = sorted(folder.glob("stream-*.jsonl"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))
    files = numbered + ([folder / "stream.jsonl"] if (folder / "stream.jsonl").exists() else [])
    out = {"session": None, "week": None, "turns": 0, "tokens": 0, "cost": 0.0}
    seen = set()
    for path in files:
        run_turns, result = 0, None
        with open(path, encoding="utf-8", errors="replace") as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(event, dict):
                    continue
                info = event.get("rate_limit_info")
                if isinstance(info, dict):
                    for key, name in WINDOWS.items():
                        window = (info.get("unifiedWindows") or {}).get(key)
                        if window and window.get("utilization") is not None:
                            now = window["utilization"]
                            if out[name] is None:
                                out[name] = {"start": now, "now": now, "resetsAt": window.get("resetsAt")}
                            else:
                                out[name].update(now=now, resetsAt=window.get("resetsAt"))
                kind = event.get("type")
                if kind == "assistant":
                    message = event.get("message") or {}
                    key = message.get("id")
                    if key and key not in seen:
                        seen.add(key)
                        usage = message.get("usage") or {}
                        out["tokens"] += sum(usage.get(k) or 0 for k in (
                            "input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
                        if event.get("parent_tool_use_id") is None:
                            run_turns += 1
                elif kind == "result":
                    result = event
        out["turns"] += (result.get("num_turns") or run_turns) if result else run_turns
        out["cost"] += (result.get("total_cost_usd") or 0) if result else 0
    print(json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1])
