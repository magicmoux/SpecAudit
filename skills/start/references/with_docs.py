#!/usr/bin/env python3
"""Run a command with SPEC_DOCS set, so that the guards that read the document read another version of it.

  python3 with_docs.py <path in the project>=<file to read> [<path>=<file> ...] -- <command> [<args> ...]
  python3 with_docs.py selection.md=/abs/scratch/orig.md -- pytest -q -p no:cacheprovider spec-guards/test_F_1_1_text.py

The audit session may run only the forms its allow list names: `env SPEC_DOCS=... pytest` is not one of them, and
allowing `env SPEC_DOCS=*` would allow any command after it. This script is copied into the scratch root, where the
interpreter rule already lets it run, and it runs the command it is given with SPEC_DOCS added to the environment
(merged with any SPEC_DOCS already set), without a shell. Its exit code is the command's.
"""
import json
import os
import subprocess
import sys


def main(argv):
    if "--" not in argv or argv.index("--") == len(argv) - 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    sep = argv.index("--")
    docs = json.loads(os.environ.get("SPEC_DOCS", "{}"))
    for pair in argv[:sep]:
        path, eq, target = pair.partition("=")
        if not eq or not path or not target:
            print(f"not a <path>=<file> pair: {pair!r}", file=sys.stderr)
            return 2
        if not os.path.isfile(target):
            print(f"no such file to read for {path}: {target}", file=sys.stderr)
            return 2
        docs[path] = os.path.abspath(target)
    env = dict(os.environ, SPEC_DOCS=json.dumps(docs), PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(argv[sep + 1:], env=env).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
