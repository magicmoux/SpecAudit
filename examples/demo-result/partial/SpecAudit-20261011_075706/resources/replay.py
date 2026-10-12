#!/usr/bin/env python3
"""Replay the guard corpus of an audit results folder, on the fixed document or on the original one.

  python3 resources/replay.py --on fixed    every guard must pass: the fixes hold
  python3 resources/replay.py --on source   each fixed error's text check must fail: the corpus detects the error
                                            in the document itself, not only in an encoding of its statement

Run it from the root of the results folder. It reads resources/manifest.json, written at closing:

  {
    "documents": {"selection.md": {"source": "source/selection.md", "fixed": "selection.fixed.md"}},
    "guards": [
      {"error": "F-1-1", "file": "resources/corpus/test_F_1_1.py", "text": false,
       "command": ["pytest", "-q", "-p", "no:cacheprovider", "resources/corpus/test_F_1_1.py"]},
      {"error": "F-1-1", "file": "resources/corpus/test_F_1_1_text.py", "text": true, "command": ["..."]}
    ]
  }

Each guard runs with SPEC_DOCS set to a JSON map from each document's path in the project to the copy to read,
which is how a guard that reads the text finds it (see the register format's guard example). The exit code is 0
when every guard behaves as expected in the chosen mode, 1 otherwise, 2 on a malformed folder.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--on", choices=["fixed", "source"], default="fixed")
    args = parser.parse_args()

    root = Path.cwd()
    try:
        manifest = json.loads((root / "resources" / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"cannot read resources/manifest.json from {root}: {exc}", file=sys.stderr)
        return 2

    docs = {}
    for path, copies in manifest["documents"].items():
        target = copies.get(args.on)
        if not target or not (root / target).is_file():
            print(f"no {args.on} copy of {path} in this folder ({target or 'not recorded'})", file=sys.stderr)
            return 2
        docs[path] = str(root / target)
    env = dict(os.environ, SPEC_DOCS=json.dumps(docs), PYTHONDONTWRITEBYTECODE="1")

    rows, unexpected = [], 0
    for guard in manifest["guards"]:
        run = subprocess.run(guard["command"], cwd=root, env=env, capture_output=True, text=True)
        passed = run.returncode == 0
        # On the original, a text check must fail (the error is there); a check of the encoded statement passes
        # either way, since it shows the original statement false on its witness.
        expected = not (args.on == "source" and guard.get("text"))
        ok = passed == expected
        unexpected += not ok
        rows.append((guard["error"], guard["file"], "text" if guard.get("text") else "statement",
                     "green" if passed else "red", "green" if expected else "red", "ok" if ok else "UNEXPECTED"))

    if args.on == "source":
        # A fixed error with no text check cannot go red on the original: the corpus would not see the text revert.
        with_text = {g["error"] for g in manifest["guards"] if g.get("text")}
        for error in sorted({g["error"] for g in manifest["guards"]} - with_text - {"lint"}):
            rows.append((error, "-", "text", "-", "red", "NO TEXT CHECK"))
            unexpected += 1

    widths = [max(len(str(r[i])) for r in rows + [("Error", "Guard", "Checks", "Got", "Expected", "")])
              for i in range(6)]
    for row in [("Error", "Guard", "Checks", "Got", "Expected", "")] + rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip())
    print(f"\n{len(rows) - unexpected}/{len(rows)} as expected on the {args.on} document.")
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main())
