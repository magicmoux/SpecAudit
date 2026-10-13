#!/usr/bin/env python3
"""Hook of the audit session: keep each agent's journal in its scratch directory, whatever the agent does.

  python3 journal.py [--stream <stream.jsonl> --pause-at <threshold> --flag <pause-requested>] [--ended <file>]
                     [--stop <stop-requested>] [--lock <agent-running>]

Registered by the launcher (references/launch.md, step 6) for PreToolUse, PostToolUse, PostToolUseFailure, SubagentStop
and SessionEnd, it
reads the hook's JSON on stdin and writes, in the scratch directory named in the agent's message ("Scratch directory: <path>"):
  prompt.md      the agent's message, word for word, when the orchestrator launches it (PreToolUse on Agent);
  journal.jsonl  one line per tool call of the agent: the tool, its input and the start of its output (PostToolUse),
                 after a launch line naming the revision (HEAD) it was launched on;
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
And it holds the audit to one agent at a time (--lock, a folder in the scratch root; SKILL.md, "One agent at a time"):
every launch runs in the foreground (run_in_background is set to false), and a launch while another agent of the audit
has not returned is refused, so that no two agents ever read the document, run an oracle or write a file at once. The
lock is a folder created by mkdir, which either creates it or fails, so two launches in one message cannot both pass;
it names the running agent's scratch directory, and is released when the Agent call returns (PostToolUse or
PostToolUseFailure), or found stale once that agent has its result.md or partial.md (a hook that did not run).
Apart from these refusals it never blocks a tool call: any error is ignored, and the exit code is 0.
"""
import json
import re
import shutil
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
STOP_ORCHESTRATOR = ("stop requested: launch no agent. Record the state of the last agent in the register, commit, set "
                     "the state to suspended (stopped on request) and end.")


ONE_AT_A_TIME = ("one agent at a time: {running} has not returned yet. Launch no other agent until its result is in "
                 "(SKILL.md, \"One agent at a time\"); never launch two in one message, nor in the background.")


def same(a, b):
    import os
    norm = lambda x: os.path.normcase(os.path.normpath(str(x)))
    return a is not None and b is not None and norm(a) == norm(b)


def take_lock(lock, scratch):
    """None when the lock is taken for this agent; otherwise the scratch directory of the agent still running.
    Claude Code may run this hook twice for one launch, side by side (the matcher names the tool under both its
    names): a second call for the same agent is the same launch, not another one, and a lock whose holder is not
    written yet belongs to a call in progress, not to a dead one."""
    lock = Path(lock)
    for _ in range(2):
        try:
            lock.mkdir(parents=True)
        except FileExistsError:
            holder = lock / "scratch"
            for _ in range(40):  # the call that created the lock is writing its holder
                if holder.exists() and holder.read_text(encoding="utf-8").strip():
                    break
                time.sleep(0.05)
            text = holder.read_text(encoding="utf-8").strip() if holder.exists() else ""
            running = Path(text) if text else None
            if same(running, scratch):
                return None
            if running is None:
                if time.time() - lock.stat().st_mtime < 10:
                    return Path("an agent being launched")
                shutil.rmtree(lock, ignore_errors=True)  # an empty lock left by a hook that died
                continue
            if (running / "result.md").exists() or (running / "partial.md").exists():
                shutil.rmtree(lock, ignore_errors=True)  # stale: its agent ended without its release
                continue
            return running
        (lock / "scratch").write_text(scratch.as_posix() if scratch else "", encoding="utf-8")
        return None
    return Path("?")


def revision(cwd):
    """The commit the agent is launched on (HEAD of the worktree), for its journal: the ground truth of the agent table."""
    import subprocess
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=cwd or None, capture_output=True, text=True,
                             timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def release_lock(lock):
    if lock:
        shutil.rmtree(lock, ignore_errors=True)


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
    orchestrator_agent = event.get("tool_name") in ("Agent", "Task") and not event.get("agent_id")
    if name == "PreToolUse" and orchestrator_agent:
        tool_input = event.get("tool_input") or {}
        prompt = tool_input.get("prompt", "")
        scratch = scratch_of(prompt)
        if args.lock:
            running = take_lock(args.lock, scratch)
            if running is not None:
                return ONE_AT_A_TIME.format(running=f"the agent of {running}")
        sent = record_prompt(scratch, prompt) if scratch else prompt
        pause = paused(args)
        if pause:
            release_lock(args.lock)
            if scratch:
                append(scratch, {"event": "refused", "pause": pause})
            return (f"paused: usage limit ({pause.get('window')} window at {pause.get('utilization')}), resumes at "
                    f"{pause.get('resumeAtLocal')}. Launch no other agent: record the pause in the register and stop "
                    f"(SKILL.md, \"Agent journal\").")
        if scratch:
            append(scratch, {"event": "launch", "description": tool_input.get("description"),
                             "revision": revision(event.get("cwd"))})
        updated = {**tool_input, "prompt": sent}
        if args.lock:
            updated["run_in_background"] = False
        if updated != tool_input:
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                           "updatedInput": updated}}
    elif name in ("PostToolUse", "PostToolUseFailure") and orchestrator_agent:
        release_lock(args.lock)
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
    ap.add_argument("--lock")
    args = ap.parse_args()  # before stdin: --help must not wait for an event
    reason = None
    try:
        reason = handle(json.loads(sys.stdin.read()), args)
    except Exception:  # a journal must never stop the audit
        pass
    if isinstance(reason, dict):
        print(json.dumps(reason))
    elif reason:
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)
