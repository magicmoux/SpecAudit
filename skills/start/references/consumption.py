#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
"""Measure what an audit session consumed, from its streams: tokens per agent, cost per model, share of the usage windows.

  python3 consumption.py <launch folder | stream.jsonl>... [--config-dir <folder>] [--no-transcripts]
                         [--report <report.md>] [--json]

Run by the launcher once the audit session has ended (references/launch.md, step 6). A launch folder stands for all its
streams, in order: stream-1.jsonl, stream-2.jsonl… (the runs before each --resume, moved aside by the launcher), then
stream.jsonl, the last run. Prints the report's "## Consumption" section in Markdown; with --json, one JSON object
instead; with --report, also puts the section in place of the one the audit session wrote in that report.

What each figure rests on, in a `claude -p --output-format stream-json --verbose` stream:
  - every assistant message carries its usage; the same message can appear on several lines, so it is counted once,
    by message.id. Its input, cache write and cache read are exact; its output is the count at the start of
    streaming, short of the real one, so it is not used;
  - parent_tool_use_id is null for the orchestrator, and for an agent's messages the id of the Agent tool_use that
    launched it, whose prompt names the agent's scratch directory ("Scratch directory: <path>"), as in the register's
    agent table;
  - each turn of the orchestrator ends with a `result` event whose usage is that turn's, the exact output included;
    its modelUsage (per model) and total_cost_usd are cumulative over the session, so the last one is taken;
  - an agent's exact output is in its transcript, <config>/projects/*/<session>/subagents/agent-<agentId>.jsonl, when
    it can be found (--config-dir, else $CLAUDE_CONFIG_DIR, else ~/.claude); otherwise it is left unattributed;
  - rate_limit_event gives the utilization of the account's two windows, with the time each resets.
Rows sum to the total of modelUsage: what no row accounts for goes to a "not attributed" row. Cost is known per model
and in total only; no cost per agent is computed.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from journal import SCRATCH  # noqa: E402  the pattern the agents' journal reads the scratch directory with

FIELDS = ("input", "cache_write", "cache_read", "output")
USAGE_KEYS = {"input": "input_tokens", "cache_write": "cache_creation_input_tokens",
              "cache_read": "cache_read_input_tokens", "output": "output_tokens"}
MODEL_KEYS = {"input": "inputTokens", "cache_write": "cacheCreationInputTokens",
              "cache_read": "cacheReadInputTokens", "output": "outputTokens"}
WINDOWS = {"five_hour": "session", "seven_day": "week"}
WINDOW_LABEL = {"session": "Session (5 h)", "week": "Week"}


def zero():
    return dict.fromkeys(FIELDS, 0)


def add(a, b):
    for k in FIELDS:
        a[k] += b.get(k) or 0
    return a


def usage_of(u, keys=USAGE_KEYS):
    return {k: int((u or {}).get(key) or 0) for k, key in keys.items()}


def streams_of(paths):
    out = []
    for p in map(Path, paths):
        if p.is_dir():
            numbered = sorted((f for f in p.glob("stream-*.jsonl") if re.fullmatch(r"stream-\d+\.jsonl", f.name)),
                              key=lambda f: int(re.search(r"\d+", f.name).group()))
            out += numbered + ([p / "stream.jsonl"] if (p / "stream.jsonl").exists() else [])
        elif p.exists():
            out.append(p)
    return out


def events(path):
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if isinstance(e, dict):
            yield e


def agent_name(tool_input):
    m = SCRATCH.search(tool_input.get("prompt") or "")
    if m:
        parts = m.group(1).strip().strip("`'\"").replace("\\", "/").rstrip("/").split("/")
        return parts[-1], (parts[-2] if len(parts) > 1 else "")
    return tool_input.get("description") or "agent", ""


def role_of(name, parent, tool_input):
    kind = (tool_input.get("subagent_type") or "").split(":")[-1]
    if parent == "preflight":
        return "preflight"
    if (tool_input.get("prompt") or "").lstrip().lower().startswith("guard review"):
        return "guard review"
    if name.startswith("probe-"):
        return "probe"
    for r in ("reviewer", "adjudicator"):
        if name.startswith(r) or r in kind:
            return r
    return kind or "agent"


def transcript_output(path):
    """Output tokens of a transcript, each message counted once: the transcript records the final usage."""
    seen = {}
    for e in events(path):
        if e.get("type") == "assistant":
            m = e.get("message") or {}
            seen[m.get("id") or id(e)] = int((m.get("usage") or {}).get("output_tokens") or 0)
    return sum(seen.values())


def find_transcripts(config_dirs, session):
    for c in config_dirs:
        for d in (Path(c) / "projects").glob(f"*/{session}"):
            if (d / "subagents").is_dir():
                return d / "subagents"
    return None


def read_stream(path, config_dirs):
    """One run of the audit session: its rows, its totals, its cost and its windows."""
    s = {"file": Path(path).as_posix(), "session": None, "messages": {}, "agents": {}, "order": [], "results": [],
         "windows": {"session": [], "week": []}, "after_result": False}
    for e in events(path):
        t = e.get("type")
        if t == "system" and e.get("subtype") == "init":
            s["session"] = s["session"] or e.get("session_id")
        elif t == "assistant":
            m = e.get("message") or {}
            s["messages"][m.get("id") or id(e)] = (e.get("parent_tool_use_id"), usage_of(m.get("usage")), m.get("model"))
            s["after_result"] = True
            for b in m.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Agent", "Task") \
                        and b.get("id") not in s["agents"]:
                    s["agents"][b["id"]] = {"input": b.get("input") or {}, "agentId": None, "model": None}
                    s["order"].append(b["id"])
        elif t == "user":
            r = e.get("tool_use_result")
            content = (e.get("message") or {}).get("content")
            if isinstance(r, dict) and r.get("agentId") and isinstance(content, list):
                for b in content:
                    a = s["agents"].get(b.get("tool_use_id")) if isinstance(b, dict) else None
                    if a:
                        a["agentId"], a["model"] = r["agentId"], r.get("resolvedModel")
        elif t == "system" and e.get("subtype") == "task_started" and e.get("tool_use_id") in s["agents"]:
            s["agents"][e["tool_use_id"]]["agentId"] = s["agents"][e["tool_use_id"]]["agentId"] or e.get("task_id")
        elif t == "result":
            s["results"].append(e)
            s["after_result"] = False
        elif t == "rate_limit_event":
            for key, name in WINDOWS.items():
                w = ((e.get("rate_limit_info") or {}).get("unifiedWindows") or {}).get(key)
                if w and w.get("utilization") is not None:
                    s["windows"][name].append((float(w["utilization"]), w.get("resetsAt")))
    s["subagents"] = find_transcripts(config_dirs, s["session"]) if s["session"] and config_dirs else None
    return s


def window_share(seen):
    """The run's share of one window, in points of utilization, or why there is none."""
    if not seen:
        return {"first": None, "last": None, "share": None, "reason": "no rate-limit event in the stream"}
    (first, r0), (last, r1) = seen[0], seen[-1]
    out = {"first": first, "last": last, "share": None, "reason": None}
    if r0 != r1:
        out["reason"] = f"the window reset during the run, at {local(r0)}"
    else:
        out["share"] = round((last - first) * 100, 1)
    return out


def local(epoch):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(epoch)) if epoch else "unknown time"


def measure(paths, config_dirs):
    streams = [read_stream(p, config_dirs) for p in streams_of(paths)]
    orchestrator = {"name": "orchestrator", "role": "orchestrator", "models": set(), **zero(), "output_exact": True}
    rows, total, cost, models_cost, notes = [], zero(), 0.0, {}, []
    thinking, cost_basis = 0, set()
    for n, s in enumerate(streams, 1):
        for parent, u, model in s["messages"].values():
            if parent is None:
                add(orchestrator, {**u, "output": 0})
                orchestrator["models"].add(model)
        orchestrator["output"] += sum(int((r.get("usage") or {}).get("output_tokens") or 0) for r in s["results"])
        for tid in s["order"]:
            a = s["agents"][tid]
            name, parent = agent_name(a["input"])
            row = {"name": name, "role": role_of(name, parent, a["input"]), "models": set(), **zero(),
                   "output_exact": False}
            if parent.startswith("iter-"):
                row["role"] += f", {parent}"
            for p, u, model in s["messages"].values():
                if p == tid:
                    add(row, {**u, "output": 0})
                    row["models"].add(model)
            tr = s["subagents"] / f"agent-{a['agentId']}.jsonl" if s["subagents"] and a["agentId"] else None
            if tr and tr.exists():
                row["output"], row["output_exact"] = transcript_output(tr), True
            if a["model"]:
                row["models"].add(a["model"])
            if any(row[k] for k in FIELDS):
                rows.append(row)
        last = s["results"][-1] if s["results"] else None
        if last:
            run_total = zero()
            for model, mu in (last.get("modelUsage") or {}).items():
                add(run_total, usage_of(mu, MODEL_KEYS))
                models_cost[model] = models_cost.get(model, 0.0) + float(mu.get("costUSD") or 0)
                thinking += int(mu.get("thinkingTokens") or 0)
                cost_basis.add(mu.get("costBasis"))
            cost += float(last.get("total_cost_usd") or 0)
            if s["after_result"]:
                notes.append(f"run {n} ended after its last `result` event: its last messages are counted in tokens "
                             "where the stream shows them, not in its cost")
        else:
            run_total = None
            notes.append(f"run {n} has no `result` event (the process was killed): its tokens are those the stream "
                         "shows, without the agents' output, and its cost is unknown")
        s["total"] = run_total
    attributed = zero()
    for r in [orchestrator, *rows]:
        add(attributed, r)
    measured = zero()
    for s in streams:
        if s["total"]:
            add(measured, s["total"])
    # Runs without a result have no measured total: their rows stand for it.
    unmeasured = zero()
    for s in streams:
        if not s["total"]:
            for p, u, _ in s["messages"].values():
                add(unmeasured, {**u, "output": 0})
            unmeasured["output"] += sum(int((r.get("usage") or {}).get("output_tokens") or 0) for r in s["results"])
    for k in FIELDS:
        total[k] = max(measured[k] + unmeasured[k], attributed[k])
    rest = {k: total[k] - attributed[k] for k in FIELDS}
    grand = sum(total.values())

    def finish(r):
        r = dict(r)
        r["model"] = ", ".join(sorted(m for m in r.pop("models") if m)) or "—"
        r["total"] = sum(r[k] for k in FIELDS)
        r["share"] = round(100 * r["total"] / grand, 1) if grand else 0.0
        return r

    out_rows = [finish(orchestrator)] + [finish(r) for r in rows]
    unattributed = finish({"name": "not attributed", "role": "", "models": set(), **rest, "output_exact": True}) \
        if any(rest.values()) else None
    windows = {}
    for w in ("session", "week"):
        runs = [window_share(s["windows"][w]) for s in streams]
        shares = [r["share"] for r in runs]
        if runs and all(x is not None for x in shares):
            windows[w] = {"runs": runs, "share": round(sum(shares), 1), "reason": None}
        else:
            why = "; ".join(f"run {i}: {r['reason']}" for i, r in enumerate(runs, 1) if r["reason"]) or "no stream"
            windows[w] = {"runs": runs, "share": None, "reason": why}
    return {"streams": [s["file"] for s in streams], "rows": out_rows, "unattributed": unattributed,
            "total": {**total, "total": grand, "thinking": thinking},
            "output_from_transcripts": all(r["output_exact"] for r in out_rows),
            "cost": {"total": round(cost, 4), "models": {m: round(c, 4) for m, c in models_cost.items()},
                     "basis": ", ".join(sorted(b for b in cost_basis if b)) or None},
            "windows": windows, "notes": notes, "index": None}


def num(n):
    return f"{n:,}"


def tokens_short(n):
    return f"{n / 1e6:.2f} M" if n >= 1e6 else f"{n / 1e3:.1f} k" if n >= 1e3 else str(n)


def points(x):
    return f"{x:g} point{'' if abs(x) == 1 else 's'}"


def pct(x):
    return "—" if x is None else f"{x * 100:.0f} %"


def index_cell(c):
    w = c["windows"]["week"]
    week = f"{points(w['share'])} of the week window" if w["share"] is not None else "week window share not measured"
    return f"{tokens_short(c['total']['total'])} tokens, ${c['cost']['total']:.2f}, {week}"


def markdown(c):
    runs = len(c["streams"])
    L = ["## Consumption", ""]
    if not runs:
        L += ["Not measured: no stream of the audit session was found.", ""]
        return "\n".join(L)
    L += [f"Measured by the launcher once the audit session ended, from its stream-json output ({runs} run"
          f"{'s' if runs > 1 else ''}{': the launch and ' + str(runs - 1) + ' resume' + ('s' if runs > 2 else '') if runs > 1 else ''}).",
          "",
          "| Agent | Role | Model | Input | Cache write | Cache read | Output | Total | Share |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in c["rows"] + ([c["unattributed"]] if c["unattributed"] else []):
        out = num(r["output"]) if r["output_exact"] else "—"
        L.append(f"| {r['name']} | {r['role']} | {r['model']} | {num(r['input'])} | {num(r['cache_write'])} | "
                 f"{num(r['cache_read'])} | {out} | {num(r['total'])} | {r['share']:.1f} % |")
    t = c["total"]
    L += [f"| **Total** | | | {num(t['input'])} | {num(t['cache_write'])} | {num(t['cache_read'])} | {num(t['output'])} | "
          f"{num(t['total'])} | 100 % |", ""]
    L.append(f"Total: {num(t['total'])} tokens. Output includes thinking ({num(t['thinking'])} tokens in all). "
             "Cache reads are counted in tokens like the rest, but cost far less than input or output tokens: "
             "the share of tokens is not the share of cost.")
    if c["unattributed"]:
        L.append("\"Not attributed\" is what the total counts and no row does: "
                 + ("requests outside the orchestrator's and the agents' messages." if c["output_from_transcripts"] else
                    "the output of the agents marked \"—\", whose exact figure only their transcripts hold, which were "
                    "not found, and any request outside the orchestrator's and the agents' messages."))
    L += ["", "| Model | Cost (USD) |", "|---|---|"]
    for m, v in sorted(c["cost"]["models"].items()):
        L.append(f"| {m} | {v:.2f} |")
    L += [f"| **Total** | {c['cost']['total']:.2f} |", "",
          "Cost as Claude Code reports it at the end of each run" + (f" ({c['cost']['basis']} price)" if c["cost"]["basis"] else "")
          + ", per model and in total only: the stream gives no cost per agent, and none is estimated here.", "",
          "| Window | Run | First | Last | Share of the audit |", "|---|---|---|---|---|"]
    for w in ("session", "week"):
        for i, r in enumerate(c["windows"][w]["runs"], 1):
            share = points(r["share"]) if r["share"] is not None else r["reason"]
            L.append(f"| {WINDOW_LABEL[w]} | {i} | {pct(r['first'])} | {pct(r['last'])} | {share} |")
        tw = c["windows"][w]
        if runs > 1:
            share = points(tw["share"]) if tw["share"] is not None else f"not measured: {tw['reason']}"
            L.append(f"| {WINDOW_LABEL[w]} | all | | | {share} |")
    L += ["", "A window's share is its utilization at the last request of a run minus that at the first, in points, "
          "summed over the runs; a run during which the window reset has none. Any other activity on the same account "
          "meanwhile (other sessions, other audits) is counted in it too."]
    for n in c["notes"]:
        L.append(f"Note: {n}.")
    return "\n".join(L) + "\n"


def replace_section(report, section):
    text = Path(report).read_text(encoding="utf-8")
    pattern = re.compile(r"^## Consumption[ \t]*\n.*?(?=^## |\Z)", re.M | re.S)
    if pattern.search(text):
        text = pattern.sub(lambda _: section.rstrip("\n") + "\n\n", text, count=1)
    else:
        anchor = re.search(r"^## Branch and closing", text, re.M)
        at = anchor.start() if anchor else len(text)
        text = text[:at] + section.rstrip("\n") + "\n\n" + text[at:]
    Path(report).write_text(text, encoding="utf-8", newline="\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--config-dir")
    ap.add_argument("--no-transcripts", action="store_true")
    ap.add_argument("--report")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    dirs = [] if a.no_transcripts else [d for d in (a.config_dir, os.environ.get("CLAUDE_CONFIG_DIR"),
                                                    str(Path.home() / ".claude")) if d]
    c = measure(a.paths, dirs)
    c["index"] = index_cell(c) if c["streams"] else "not measured"
    md = markdown(c)
    if a.report:
        replace_section(a.report, md)
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(c, indent=1) if a.json else md, end="" if not a.json else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
