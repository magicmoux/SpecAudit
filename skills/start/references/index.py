#!/usr/bin/env python3
"""Write one audit's entry in the project's index, SPECAUDITS.md, under its lock, and commit it.

  python3 index.py <original repository> --entry <entry.md> --message "<commit message>" [--add <path>...] [--no-commit]
                  [--register <register.md>]

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

Each entry written is also recorded in the index of every audit on this machine, ~/.specaudit/audits.json, one entry
per audit keyed by its repository and stamp: the repository, the worktree, the register's path, the audit's state, the
id of the session that launched it, and when it was last written. It only points: the register, in the worktree, stays
the audit's one source of truth, and a monitor watching another folder, such as the optional specaudit-monitor mod,
reads it from there, for every audit at once. The register is the one given with --register, else register.md next to
the entry file (spec-audit/<slug>/ in the worktree). This record is best effort: without the mod nothing reads it, and
a record that cannot be written changes nothing to SPECAUDITS.md or to the exit code. The single-audit beacon of earlier
versions, ~/.specaudit/beacon.json (the repository, the audit's identifier, the time), which names only the last audit
indexed, so that two audits run side by side hide each other, is still written, the same best effort, for the monitor
versions that read only it (specaudit-monitor up to 0.14); it goes once the monitor reads audits.json.
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
    """Names the repository whose index was just written, for a monitor that reads only it; any failure is ignored."""
    try:
        path = Path.home() / ".specaudit" / "beacon.json"
        path.parent.mkdir(exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"repo": repo.resolve().as_posix(), "id": ident, "at": int(time.time())}),
                       encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        pass


RESULT = re.compile(r"^\|[^|]*\|[^|]*\|[^|]*\| *([A-Z]+)(?: — ([^|]*?))? *\|")
KEEP_CLOSED_S = 30 * 24 * 3600


def registered(register, result):
    """What audits.json records of the register: its worktree, document, launcher and state ({} without a register)."""
    try:
        text = register.read_text(encoding="utf-8")
    except (OSError, ValueError):
        text = ""
    field = lambda pattern: (m.group(1).strip() if (m := re.search(pattern, text, re.M)) else None)
    out = {"worktree": field(r"^- Worktree: (.+?), branch "), "document": field(r"^- Document\(s\): (.+)$"),
           "launcher": field(r"^- Session: ([^,\s]+)"), "state": field(r"^- Session: .*?state: (.+)$")}
    status, detail = result
    # The index is the later word at closing, when the register may still say running: an audit whose result is final
    # is closed; one the result says is running or suspended keeps the register's state, or takes the result's.
    if status in ("FINISHED", "FAILED") or (status == "INTERRUPTED" and not (detail or "").startswith("suspended")):
        out["state"] = "closed"
    elif not out["state"]:
        out["state"] = "running" if status == "RUNNING" else "suspended" if status == "INTERRUPTED" else None
    return out


def record(repo, ident, register, row, results=None):
    """Records the audit in ~/.specaudit/audits.json, under its own short lock; any failure is ignored."""
    home = Path.home() / ".specaudit"
    path, guard = home / "audits.json", home / "audits.json.lock"
    held = False
    try:
        home.mkdir(exist_ok=True)
        for _ in range(20):
            try:
                os.mkdir(guard)
                held = True
                break
            except FileExistsError:
                try:
                    if time.time() - guard.stat().st_mtime > 60:
                        os.rmdir(guard)
                        continue
                except FileNotFoundError:
                    continue
                time.sleep(0.5)
        if not held:
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            audits = data["audits"] if isinstance(data, dict) and isinstance(data.get("audits"), dict) else {}
        except (OSError, ValueError):
            audits = {}
        now = int(time.time())
        repo_s = repo.resolve().as_posix()
        stamp = ident[len("SpecAudit-"):]
        m = RESULT.match(row)
        entry = {"repo": repo_s, "id": ident, "stamp": stamp,
                 "register": register.resolve().as_posix() if register.is_file() else None,
                 **registered(register, (m.group(1), m.group(2)) if m else (None, None)),
                 "result": " — ".join(g.strip() for g in m.groups() if g) if m else None, "updatedAt": now}
        if results:
            entry["results"] = results.resolve().as_posix()
        audits[f"{repo_s}#{stamp}"] = entry
        # An audit closed a month ago is dropped: SPECAUDITS.md and its results folder keep it.
        audits = {k: v for k, v in audits.items() if not (isinstance(v, dict) and v.get("state") == "closed"
                                                          and now - (v.get("updatedAt") or 0) > KEEP_CLOSED_S)}
        tmp = home / f"audits.json.{os.getpid()}.tmp"
        tmp.write_text(json.dumps({"version": 1, "audits": audits}, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        pass
    finally:
        if held:
            try:
                os.rmdir(guard)
            except OSError:
                pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo")
    ap.add_argument("--entry", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--add", nargs="*", default=[])
    ap.add_argument("--no-commit", action="store_true")
    ap.add_argument("--register", help="the audit's register (default: register.md next to the entry file)")
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
        results = next((repo / p for p in a.add if Path(p).name == ident and (repo / p).is_dir()), None)
        record(repo, ident, Path(a.register) if a.register else Path(a.entry).parent / "register.md", row, results)
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
