#!/usr/bin/env python3
"""Build the audit session's protocol.md: what its orchestrator rereads at every turn, and nothing else.

  python3 protocol.py <skill folder> <launch folder> <protocol folder> [--fail-fast] [--formal-oracle]

The orchestrator's system prompt is sent again with every one of its turns, so each section it never or rarely needs is
paid for once per turn of the whole audit (on the demo, about 60 turns). This script writes <launch folder>/protocol.md
from SKILL.md, the profile and references/register.md, leaving out the sections only the launcher or a rare case needs,
which it writes instead to <protocol folder>/on-demand.md, named in a closing line so that the orchestrator reads one
when it needs it:
  - from SKILL.md: its front matter, "Parameters", "Project configuration" (the launcher applies both and the register
    records them), "Phase 8 — Closing" (the launcher's), and "Fail-fast" unless --fail-fast;
  - from register.md: the index format and how to write it (the launcher's), the results folder's manifest (closing),
    the corpus error entry (read with corpus-errors.md, when a guard is suspect), and the Lean guard example unless
    --formal-oracle (the oracle table has a formal oracle).
Sections are split on "## " headings outside code fences. Exit code 2 when a section to leave out is not found: the
skill changed, and this list must follow it.
"""
import argparse
import re
import sys
from pathlib import Path


def sections(text):
    """[(heading or None, body)] split on '## ' lines outside ``` fences; the first item is the text before them."""
    out, head, buf, fenced = [], None, [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            out.append((head, "\n".join(buf)))
            head, buf = line[3:].strip(), [line]
        else:
            buf.append(line)
    out.append((head, "\n".join(buf)))
    return out


def split(text, leave_out):
    kept, left, missing = [], [], set(leave_out)
    for head, body in sections(text):
        match = next((p for p in leave_out if head and re.match(p, head)), None)
        if match:
            left.append(body)
            missing.discard(match)
        else:
            kept.append(body)
    return "\n".join(kept), left, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("skill")
    ap.add_argument("launch")
    ap.add_argument("protocol")
    ap.add_argument("--fail-fast", action="store_true")
    ap.add_argument("--formal-oracle", action="store_true")
    a = ap.parse_args()
    skill = Path(a.skill)
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)  # front matter: the skill's description, for triggering
    out_skill = [r"Parameters$", r"Project configuration$", r"Phase 8\b"] + ([] if a.fail_fast else [r"Fail-fast$"])
    out_register = [r"Index of the audits", r"Corpus error entry$", r"Manifest of a results folder"] \
        + ([] if a.formal_oracle else [r"Guard file \(Lean example"])
    kept_skill, left_skill, miss_skill = split(text, out_skill)
    kept_reg, left_reg, miss_reg = split((skill / "references" / "register.md").read_text(encoding="utf-8"), out_register)
    if miss_skill or miss_reg:
        print("protocol: sections not found: " + ", ".join(sorted(miss_skill | miss_reg)), file=sys.stderr)
        return 2
    on_demand = Path(a.protocol) / "on-demand.md"
    on_demand.parent.mkdir(parents=True, exist_ok=True)
    on_demand.write_text("# Sections of the protocol left out of protocol.md\n\n"
                         + "\n\n".join(left_skill + left_reg) + "\n", encoding="utf-8")
    names = [re.match(r"## (.*)", s).group(1).strip() for s in left_skill + left_reg]
    note = (f"\n\nLeft out of this prompt, since you need them rarely or never: {'; '.join(names)}. They are in "
            f"`{on_demand.as_posix()}`: read the one you need when a step names it, and only then.\n")
    profile = (skill / "profiles" / "formal.md").read_text(encoding="utf-8")
    protocol = Path(a.launch) / "protocol.md"
    protocol.parent.mkdir(parents=True, exist_ok=True)
    protocol.write_text(kept_skill.strip() + "\n\n" + profile.strip() + "\n\n" + kept_reg.strip() + note, encoding="utf-8")
    print(f"protocol.md: {protocol.stat().st_size} bytes; on-demand.md: {on_demand.stat().st_size} bytes "
          f"({len(names)} sections)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
