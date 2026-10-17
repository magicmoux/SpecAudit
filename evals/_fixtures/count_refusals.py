# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
"""Count the tool calls refused by the permission system in the transcripts of a Claude Code project folder.

  python3 count_refusals.py <~/.claude/projects/<project>>      prints the count, then one line per refusal

A refusal is a tool result marked as an error whose text begins with "Permission to use": counting the files that
merely contain that phrase would also count a register that quotes a refusal, which the audit is asked to do.
"""
import json
import sys
from pathlib import Path

refusals = []
for path in sorted(Path(sys.argv[1]).rglob("*.jsonl")):
    calls = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        content = event.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if part.get("type") == "tool_use":
                calls[part.get("id")] = f"{part.get('name')} {json.dumps(part.get('input'))[:160]}"
            elif part.get("type") == "tool_result" and part.get("is_error") \
                    and str(part.get("content")).startswith("Permission to use"):
                refusals.append(f"{path.name}: {calls.get(part.get('tool_use_id'), '?')}")
print(len(refusals))
for r in refusals:
    print(r)
