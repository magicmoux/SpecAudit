#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
"""Check that every person who changed a file in a pull request is credited for it.

  python3 attribution.py <base> [<head>]

For each commit in <base>..<head> (merges left out), its author and its `Co-authored-by:` people, through .mailmap,
are the people who changed the files the commit adds, modifies or renames. Each of them must appear in a
`SPDX-FileCopyrightText:` line of each such file still present at <head>: the file's own header for a code file, or the
last [[annotations]] entry of REUSE.toml whose path matches it (CONTRIBUTING.md, "Credit"). AI tools are not people:
an identity with the e-mail noreply@anthropic.com or a name ending in [bot] is left out, and an `Assisted-by:` trailer
is not read. LICENSE, LICENSES/ and REUSE.toml are not checked: crediting oneself happens there.

A name is credited when it appears, ignoring case, in one of the file's copyright lines. Exit code 1, with the files
and the people missing, when someone is not credited; 2 on a usage or git error.
"""
import re
import subprocess
import sys
import tomllib
from pathlib import Path

AI_EMAILS = {"noreply@anthropic.com"}
EXEMPT = re.compile(r"^(LICENSE|LICENSES/.*|REUSE\.toml)$")
HEADER_LINES = 20


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"attribution: git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def mailmap(name, email):
    out = git("check-mailmap", f"{name} <{email}>").strip()
    m = re.match(r"^(.*?)\s*<(.*)>$", out)
    return (m.group(1), m.group(2)) if m else (name, email)


def people(commit):
    """The people of a commit: its author and its Co-authored-by trailers, without AI tools."""
    fmt = "%an%x00%ae%x00%(trailers:key=Co-authored-by,valueonly,separator=%x01)"
    an, ae, co = git("show", "-s", f"--format={fmt}", commit).rstrip("\n").split("\x00")
    ids = [(an, ae)]
    for value in filter(None, co.split("\x01")):
        m = re.match(r"^\s*(.*?)\s*<(.*)>\s*$", value)
        if m:
            ids.append((m.group(1), m.group(2)))
    out = set()
    for name, email in ids:
        name, email = mailmap(name, email)
        if email.lower() in AI_EMAILS or name.endswith("[bot]"):
            continue
        out.add(name)
    return out


def glob_regex(pattern):
    """REUSE.toml globs: `**` matches anything, `*` anything but `/`, `\\*` a literal star."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("\\*", i):
            out, i = out + re.escape("*"), i + 2
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def as_list(value):
    return [value] if isinstance(value, str) else list(value or [])


def annotations(root):
    f = root / "REUSE.toml"
    if not f.exists():
        return []
    entries = []
    for a in tomllib.loads(f.read_text(encoding="utf-8")).get("annotations", []):
        entries.append(([glob_regex(p) for p in as_list(a.get("path"))], a.get("precedence", "closest"),
                        as_list(a.get("SPDX-FileCopyrightText"))))
    return entries


def holders(root, path, entries):
    """The copyright lines that apply to a file, the way REUSE resolves them."""
    try:
        head = (root / path).read_text(encoding="utf-8").splitlines()[:HEADER_LINES]
    except (UnicodeDecodeError, OSError):
        head = []
    own = [m.group(1) for line in head if (m := re.search(r"SPDX-FileCopyrightText:\s*(.*)", line))]
    match = None
    for regexes, precedence, lines in entries:
        if any(r.match(path) for r in regexes):
            match = (precedence, lines)
    if match is None:
        return own
    precedence, lines = match
    if precedence == "override" or not own:
        return lines
    return own + lines if precedence == "aggregate" else own


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__, file=sys.stderr)
        return 2
    base, head = sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "HEAD"
    root = Path(git("rev-parse", "--show-toplevel").strip())
    changed = {}
    for commit in git("rev-list", "--no-merges", f"{base}..{head}").split():
        who = people(commit)
        files = git("diff-tree", "--no-commit-id", "--name-only", "-r", "--diff-filter=AMR", "-z", commit)
        for path in filter(None, files.split("\x00")):
            changed.setdefault(path, set()).update(who)
    entries = annotations(root)
    missing = {}
    for path, who in sorted(changed.items()):
        if EXEMPT.match(path) or not (root / path).is_file():
            continue
        lines = [line.lower() for line in holders(root, path, entries)]
        absent = sorted(n for n in who if not any(n.lower() in line for line in lines))
        if absent:
            missing[path] = absent
    if not missing:
        print(f"attribution: every person who changed a file is credited ({len(changed)} files)")
        return 0
    print("attribution: people not credited in the files they changed (CONTRIBUTING.md, \"Credit\"):")
    for path, absent in missing.items():
        print(f"  {path}: {', '.join(absent)}")
    print("Add a `SPDX-FileCopyrightText: <year> <name> <<contact>>` line to the file's header, or, for a file "
          "without one, an [[annotations]] entry for it at the end of REUSE.toml. For a trivial change (a typo, a "
          "rename), a maintainer may add the `trivial` label to the pull request instead.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
