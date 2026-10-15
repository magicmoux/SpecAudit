#!/usr/bin/env python3
"""Write one audit's entry in the project's index, SPECAUDITS.md, under its lock, and commit it.

  python3 index.py <original repository> --entry <entry.md> --message "<commit message>" [--add <path>...] [--no-commit]

entry.md holds the audit's entry as references/register.md gives it: its row of the summary table (a line starting
with "| [", linked to "#specaudit-<stamp>"), a blank line, then its section, from "## SpecAudit-<stamp>" to its end.

Audits launched side by side write this file at the same moments, so every write is one locked step, done here rather
than by hand, where a read and a write chained in one command, or a lock released before the commit, has let one audit
erase another's entry:
  1. lock: the folder SPECAUDITS.md.lock, created by mkdir (retried for two minutes; removed if older than ten minutes,
     its holder having died);
  2. read the file under the lock, or create it with its header when it does not exist;
  3. replace this audit's row and section, found by its identifier, or insert them, newest first by identifier: the row
     among the table's rows, the section among the sections; no other entry's text is ever rewritten;
  4. check that every other entry is still there, unchanged;
  5. commit SPECAUDITS.md, and the paths given with --add, waiting on a held .git/index.lock;
  6. unlock, whatever happened.
Exit code 0 when the entry is written (and committed), 1 when the lock or the commit could not be had, 2 on a malformed
entry or a check that failed (nothing is written then).

Each entry written also leaves a beacon, ~/.specaudit/beacon.json (the repository, the audit's identifier, the time),
so that a monitor watching another folder, such as the optional specaudit-monitor mod, finds an audit launched in a
repository it was not looking at. It is best effort: without the mod nothing reads it, and a beacon that cannot be
written changes nothing to the index or to the exit code.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HEADER = """# SpecAudit index

Every audit launched in this project, newest first. Each entry is written at launch and updated when the audit ends, \
however it ends; an entry still RUNNING whose audit is no longer running was interrupted without a chance to say so \
(`--resume` or `/spec-audit:stop` updates it).

| Date | Audited object | Launched by | Result |
|---|---|---|---|
"""
SECTION = re.compile(r"^## (SpecAudit-\d{8}_\d{6}(?:-\d+)?)\s*$")
ROW = re.compile(r"^\| \[[^]]*\]\(#(specaudit-\d{8}_\d{6}(?:-\d+)?)\)")


def entries(text):
    """{identifier: (row, section)} of every entry of the index."""
    rows = {m.group(1).lower(): line for line in text.split("\n") if (m := ROW.match(line))}
    sections, current = {}, None
    for line in text.split("\n"):
        m = SECTION.match(line)
        if m:
            current = m.group(1)
            sections[current] = []
        elif line.startswith("# ") or (line.startswith("## ") and current):
            current = None
        elif current:
            sections[current].append(line)
    return {ident: (rows.get(ident.lower()), "\n".join(body).strip()) for ident, body in sections.items()}


def write(text, ident, row, section):
    lines = text.split("\n")
    key = f"(#{ident.lower()})"
    rows = [i for i, line in enumerate(lines) if ROW.match(line) and key in line]
    if rows:
        lines[rows[0]] = row
    else:
        sep = next(i for i, line in enumerate(lines) if re.match(r"^\|(-+\|)+\s*$", line))
        older = [i for i, line in enumerate(lines) if (m := ROW.match(line)) and m.group(1) < ident.lower()]
        last = max([sep] + [i for i, line in enumerate(lines) if ROW.match(line)])
        lines.insert(older[0] if older else last + 1, row)
    starts = [i for i, line in enumerate(lines) if SECTION.match(line)]
    own = [i for i in starts if SECTION.match(lines[i]).group(1) == ident]
    if own:
        end = next((i for i in starts if i > own[0]), len(lines))
        lines[own[0]:end] = section.split("\n") + [""]
    elif starts:
        older = [i for i in starts if SECTION.match(lines[i]).group(1).lower() < ident.lower()]
        at = older[0] if older else len(lines)
        lines[at:at] = section.split("\n") + [""]
    else:
        lines += [""] + section.split("\n")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).rstrip("\n") + "\n"


def lock(path):
    for _ in range(120):
        try:
            os.mkdir(path)
            return True
        except FileExistsError:
            try:
                if time.time() - path.stat().st_mtime > 600:
                    os.rmdir(path)
                    continue
            except FileNotFoundError:
                continue
            time.sleep(1)
    return False


def git(repo, *args):
    for _ in range(60):
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        if r.returncode == 0 or "index.lock" not in r.stderr:
            return r
        time.sleep(1)
    return r


def beacon(repo, ident):
    """Names the repository whose index was just written, for a monitor; any failure is ignored."""
    try:
        path = Path.home() / ".specaudit" / "beacon.json"
        path.parent.mkdir(exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"repo": repo.resolve().as_posix(), "id": ident, "at": int(time.time())}),
                       encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo")
    ap.add_argument("--entry", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--add", nargs="*", default=[])
    ap.add_argument("--no-commit", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo)
    entry = Path(a.entry).read_text(encoding="utf-8").strip("\n")
    row, _, section = entry.partition("\n\n")
    m_row, m_sec = ROW.match(row), SECTION.match(section.split("\n")[0])
    if not (m_row and m_sec and m_row.group(1) == m_sec.group(1).lower()):
        print("index: the entry must be its row, a blank line, then its section, with the same identifier",
              file=sys.stderr)
        return 2
    ident = m_sec.group(1)
    for p in a.add:
        folder = repo / p
        # The folder reserved at launch exists, so `cp -r <worktree>/<folder> <repo>/<folder>` nests the results one
        # level down, where the index's link, the README's paths and replay.py no longer find them.
        if folder.name.startswith("SpecAudit-") and folder.is_dir() and not (folder / "README.md").exists():
            nested = folder / folder.name
            hint = (f"; the results are nested in {p}/{folder.name}/: copy the folder's contents instead, "
                    f"`cp -r <worktree>/{folder.name}/. <repo>/{folder.name}/`") if nested.is_dir() else ""
            print(f"index: {p} has no README.md at its root{hint}; nothing written", file=sys.stderr)
            return 2
    index, guard = repo / "SPECAUDITS.md", repo / "SPECAUDITS.md.lock"
    if not lock(guard):
        print(f"index: {guard} held for two minutes; nothing written", file=sys.stderr)
        return 1
    try:
        before = index.read_text(encoding="utf-8") if index.exists() else HEADER
        after = write(before, ident, row, section)
        others_before = {k: v for k, v in entries(before).items() if k != ident}
        others_after = {k: v for k, v in entries(after).items() if k != ident}
        if others_before != others_after or ident not in entries(after):
            print("index: the check failed, another entry would change; nothing written", file=sys.stderr)
            return 2
        index.write_text(after, encoding="utf-8", newline="\n")
        print(f"index: {ident} written; {len(others_after)} other entries kept")
        beacon(repo, ident)
        if a.no_commit:
            return 0
        paths = ["SPECAUDITS.md", *a.add]
        r = git(repo, "add", "--", *paths)
        if r.returncode == 0:
            r = git(repo, "commit", "-q", "-m", a.message, "--", *paths)
        if r.returncode != 0:
            print(f"index: commit failed: {r.stderr.strip()}", file=sys.stderr)
            return 1
        print(f"index: committed ({a.message.splitlines()[0]})")
        return 0
    finally:
        os.rmdir(guard)


if __name__ == "__main__":
    sys.exit(main())
