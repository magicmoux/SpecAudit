#!/usr/bin/env python3
"""Hook of the audit session: keep each agent's journal in its scratch directory, whatever the agent does.

  python3 journal.py [--stream <stream.jsonl> --pause-at <threshold> --flag <pause-requested>] [--ended <file>]
                     [--stop <stop-requested>]

Registered by the launcher (references/launch.md, step 6) for PreToolUse, PostToolUse, SubagentStop and SessionEnd, it
reads the hook's JSON on stdin and writes, in the scratch directory named in the agent's message ("Scratch directory: <path>"):
  prompt.md      the agent's message, word for word, when the orchestrator launches it (PreToolUse on Agent);
  journal.jsonl  one line per tool call of the agent: the tool, its input and the start of its output (PostToolUse);
  result.md      the agent's final reply, when it ends (SubagentStop).
An agent stopped or cut by a usage limit keeps its prompt and its journal up to its last tool call, and has no
result.md: --resume relaunches exactly those agents, with their prompt, and the replacement finds the scripts and
outputs of the journal in its scratch directory. Nothing here relies on the agent or the orchestrator writing anything.

It also holds the usage threshold, so that a pause never depends on the orchestrator remembering to check for it:
before an agent's launch, it reads the session's own stream (--stream, as usage.py does); once a window reaches
--pause-at, or a pause was already requested (--flag), it writes the request and refuses the launch (exit code 2, the
reason on stderr, which the orchestrator receives as the tool's error). The refused agent keeps its prompt.md, so the
resume launches it. At the session's end (SessionEnd), it writes --ended with the reason, for the launcher.

And it carries a stop requested from above down to the agents (--stop, a file the launcher or /spec-audit:stop writes):
an agent's next tool call is refused with the instruction to reply now with its state; its reply, at its end, goes to
partial.md rather than result.md, so that the resume relaunches it, the replacement starting from that state; and the
orchestrator's next launch is refused, so that it waits for its agents, records the stop and ends. Each level ends
after the one below it has reported, instead of being cut in the middle of its reasoning.
Apart from these refusals it never blocks a tool call: any error is ignored, and the exit code is 0.
"""
import json
import re
import sys
import time
from pathlib import Path

# The path ends at the end of its line, or at a period followed by a space ("…/reviewer. Write probe.py there…").
SCRATCH = re.compile(r"Scratch directory(?: for your computations)?:\s*(.+?)(?:\.\s|\.?\s*$)", re.M)


def scratch_of(prompt):
    m = SCRATCH.search(prompt or "")
    return Path(m.group(1).strip().strip("`'\"")) if m else None


def first_prompt(transcript):
    """The agent's message: the first user message of its transcript."""
    with open(transcript, encoding="utf-8") as f:
        content = json.loads(f.readline())["message"]["content"]
    if isinstance(content, list):
        content = "\n".join(c.get("text", "") for c in content if isinstance(c, dict))
    return content


def agent_transcript(event):
    if event.get("agent_transcript_path"):
        return Path(event["agent_transcript_path"])
    main = Path(event["transcript_path"])  # <project>/<session>.jsonl; its agents: <project>/<session>/subagents/
    return main.with_suffix("") / "subagents" / f"agent-{event['agent_id']}.jsonl"


def clip(value, n):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= n else text[:n] + f"… [{len(text)} chars]"


def append(scratch, record):
    scratch.mkdir(parents=True, exist_ok=True)
    record = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
    with open(scratch / "journal.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def record_prompt(scratch, prompt):
    """Keep the agent's message, and return the one to send. A scratch directory with a prompt and no result is an
    agent to replace: it is sent its original prompt, word for word, whatever the orchestrator wrote this time, which is
    kept beside it (prompt.rewritten.md) so that the difference can be seen. A scratch directory whose agent ended
    receives a new task: the new prompt replaces the old one, kept as prompt.prev.md."""
    scratch.mkdir(parents=True, exist_ok=True)
    stored = scratch / "prompt.md"
    if stored.exists():
        original = stored.read_text(encoding="utf-8")
        if original != prompt:
            if not (scratch / "result.md").exists():
                (scratch / "prompt.rewritten.md").write_text(prompt, encoding="utf-8")
                append(scratch, {"event": "prompt replaced by the original", "kept": "prompt.rewritten.md"})
                return original
            (scratch / "prompt.prev.md").write_text(original, encoding="utf-8")
    stored.write_text(prompt, encoding="utf-8")
    return prompt


def paused(args):
    """The pause request, written if a window reached its threshold: None while the audit may go on."""
    if not (args.stream and args.flag):
        return None
    flag = Path(args.flag)
    if not flag.exists():
        from usage import decide  # beside this script, in the protocol folder
        decide(args.stream, args.pause_at, str(flag))
    return json.loads(flag.read_text(encoding="utf-8")) if flag.exists() else None


STOP_AGENT = ("stop requested: run nothing more. Reply now, and end, with your current state: what you have read, "
              "the findings or the verdict in progress with their evidence, and the scripts and outputs worth reusing. "
              "A fresh agent will resume from it.")
STOP_ORCHESTRATOR = ("stop requested: launch no agent. Wait for the agents running to reply, record their state in the "
                     "register, commit, set the state to suspended (stopped on request) and end.")


def handle(event, args):
    """Returns the reason for refusing the tool call, the hook's output that rewrites it, or None."""
    name = event.get("hook_event_name")
    stopping = bool(args.stop) and Path(args.stop).exists()
    if stopping and name == "PreToolUse":
        if event.get("agent_id"):
            scratch = scratch_of(first_prompt(agent_transcript(event)))
            if scratch:
                append(scratch, {"event": "stop requested", "refused": event.get("tool_name")})
            return STOP_AGENT
        if event.get("tool_name") in ("Agent", "Task"):
            prompt = (event.get("tool_input") or {}).get("prompt", "")
            scratch = scratch_of(prompt)
            if scratch:
                record_prompt(scratch, prompt)
                append(scratch, {"event": "refused", "stop": True})
            return STOP_ORCHESTRATOR
    if name == "PreToolUse" and event.get("tool_name") in ("Agent", "Task") and not event.get("agent_id"):
        prompt = (event.get("tool_input") or {}).get("prompt", "")
        scratch = scratch_of(prompt)
        sent = record_prompt(scratch, prompt) if scratch else prompt
        pause = paused(args)
        if pause:
            if scratch:
                append(scratch, {"event": "refused", "pause": pause})
            return (f"paused: usage limit ({pause.get('window')} window at {pause.get('utilization')}), resumes at "
                    f"{pause.get('resumeAtLocal')}. Launch no other agent: wait for those running, record the pause "
                    f"in the register and stop (SKILL.md, \"Agent journal\").")
        if scratch:
            append(scratch, {"event": "launch", "description": (event.get("tool_input") or {}).get("description")})
        if sent != prompt:
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                           "updatedInput": {**event["tool_input"], "prompt": sent}}}
    elif name == "SessionEnd" and args.ended:
        Path(args.ended).write_text(json.dumps({"reason": event.get("reason"), "t": time.strftime("%Y-%m-%dT%H:%M:%S")})
                                    + "\n", encoding="utf-8")
    elif name == "PostToolUse" and event.get("agent_id"):
        scratch = scratch_of(first_prompt(agent_transcript(event)))
        if scratch:
            append(scratch, {"tool": event.get("tool_name"), "input": clip(event.get("tool_input"), 600),
                             "output": clip(event.get("tool_response"), 1500)})
    elif name == "SubagentStop" and event.get("agent_id"):
        scratch = scratch_of(first_prompt(agent_transcript(event)))
        if scratch:
            final = "partial.md" if stopping else "result.md"
            (scratch / final).write_text(event.get("last_assistant_message") or "", encoding="utf-8")
            append(scratch, {"event": "stop", "wrote": final})


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream")
    ap.add_argument("--pause-at", default="session=75,week=50")
    ap.add_argument("--flag")
    ap.add_argument("--ended")
    ap.add_argument("--stop")
    reason = None
    try:
        reason = handle(json.loads(sys.stdin.read()), ap.parse_args())
    except Exception:  # a journal must never stop the audit
        pass
    if isinstance(reason, dict):
        print(json.dumps(reason))
    elif reason:
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)
