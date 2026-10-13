#!/usr/bin/env python3
"""Read a project's architecture, SPECAUDIT_ARCH.md, and hold the audit to it.

  python3 arch.py require  [--root <repo>]                 is there a valid architecture? (exit 2: none, 1: invalid)
  python3 arch.py show     [--root <repo>] [--config <file>] [--json]
  python3 arch.py role     [--root <repo>] <path>...       the role of each path
  python3 arch.py normative [--root <repo>] [--config <file>] <document>
                                                           the normative dependencies given to the reviewers
  python3 arch.py check    [--root <repo>] [--corpus <dir>] (--staged | --since <rev> | <path>...)
                                                           may the audit commit these changes? (exit 1: no)
  python3 arch.py hook     --root <repo> [--corpus <dir>]  PreToolUse hook of the audit session (stdin: the event)

SPECAUDIT_ARCH.md, at the root of the project, is written by /spec-audit:init or by hand. Its format, which this
script reads (the header of the file repeats it):

  ## Paths                 | Path | Role | Profile | Description |
  ## Oracles               | Path | Kind | Command | Correspondence | Guards |
  ## Normative dependencies | Document | Normative |
  ## Mapped pairs          | Document | Counterpart | Correspondence |

A path is relative to the root, with `/` as separator: `dir/` is a folder and everything under it, `*` and `?` match
within one segment, `**` across segments. Code spans are optional. When several entries match a path, the most specific
one wins: an exact file, then the longest literal part. A cell may hold several paths, separated by commas; `—` or an
empty cell means none.

What the audit may change (check, hook): the paths whose role is `audited`; the guard corpus and the guard locations of
the oracles; its own records (`spec-audit/`, `SpecAudit-*/`, `SPECAUDITS.md`); and the counterpart and correspondence
table of a mapped pair, only together with the pair's document. Everything else is read-only: `original`,
`prior-version`, `normative`, `sources`, `oracle`, `ignored`, the paths the file does not list, the architecture itself
and the orchestrator's configuration (`.specaudit.md`, `.specaudit/`).

What an agent may read (hook): everything but the results of audits (`SPECAUDITS.md`, `SpecAudit-*/`, `spec-audit/`),
the configuration (beyond the normative dependencies the architecture lists), session history (`.forge/`, `.claude/`),
and the paths marked `original`, `prior-version` or `ignored`. The orchestrator may read everything but `ignored`.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

FILE = "SPECAUDIT_ARCH.md"
ROLES = ("audited", "original", "prior-version", "normative", "sources", "oracle", "ignored")
ORACLE_KINDS = ("formal", "model", "runner")
PROFILES_DIR = Path(__file__).resolve().parent.parent / "profiles"
AUDIT_RECORDS = ("spec-audit/", "SpecAudit-*/", "SPECAUDITS.md", "SPECAUDITS.md.lock/")
CONFIGURATION = (FILE, ".specaudit.md", ".specaudit/")
HISTORY = (".forge/", ".claude/")
NONE = {"", "—", "-", "none", "n/a"}
WRITE_TOOLS = ("Edit", "Write", "NotebookEdit", "MultiEdit")
READ_TOOLS = ("Read", "Grep", "Glob")


class ArchError(Exception):
    pass


# --- Paths and patterns -------------------------------------------------------------------------------------------

def norm(path):
    p = str(path).strip().strip("`").replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p


def glob_regex(pattern):
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def matches(pattern, path):
    """Does `pattern` (a file, a folder `dir/`, or a glob) cover `path`?"""
    pattern, path = norm(pattern), norm(path)
    if not pattern:
        return False
    if pattern in (".", "./", "/"):
        return True
    base = pattern.rstrip("/")
    if any(c in base for c in "*?["):
        rx = glob_regex(base)
        parts = path.split("/")
        # A glob covers a path when it matches the path or one of its parent folders.
        return any(rx.match("/".join(parts[:n])) for n in range(1, len(parts) + 1))
    if path == base:
        return True
    return path.startswith(base + "/")


def specificity(pattern, path):
    pattern = norm(pattern)
    exact = pattern == norm(path)
    literal = re.sub(r"[*?].*", "", pattern)
    return (exact, len(literal))


def best(entries, path, key="path"):
    found = [e for e in entries if any(matches(p, path) for p in e[key])]
    if not found:
        return None
    return max(found, key=lambda e: max(specificity(p, path) for p in e[key] if matches(p, path)))


def any_match(patterns, path):
    return any(matches(p, path) for p in patterns)


# --- Reading the file ---------------------------------------------------------------------------------------------

def cells(line):
    line = line.strip()
    if not (line.startswith("|") and line.endswith("|")):
        return None
    return [c.strip() for c in line[1:-1].split("|")]


def paths_of(cell):
    if cell is None or cell.strip().lower() in NONE:
        return []
    return [norm(p) for p in re.split(r",\s*", cell) if norm(p) and norm(p).lower() not in NONE]


def value(cell):
    if cell is None:
        return None
    v = cell.strip().strip("`").strip()
    return None if v.lower() in NONE else v


def tables(text):
    """{section title (lowercase): [row dicts keyed by lowercase header]}: the first table of each `## ` section."""
    out, section, header, done, in_code = {}, None, None, set(), False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.startswith("## "):
            section, header = line[3:].strip().lower(), None
            continue
        row = cells(line)
        if section is None or section in done:
            continue
        if row is None:
            if header is not None:
                done.add(section)  # the table has ended; a second one in the section is not read
                header = None
            continue
        if header is None:
            header = [c.lower() for c in row]
            out[section] = []
        elif not all(set(c) <= set("-: ") for c in row):
            out[section].append({h: (row[i] if i < len(row) else "") for i, h in enumerate(header)})
    return out


def column(row, *names):
    for n in names:
        if n in row:
            return row[n]
    return None


def parse(text):
    t = tables(text)
    if "paths" not in t:
        raise ArchError("no `## Paths` table")
    arch = {"paths": [], "oracles": [], "normative": [], "pairs": [], "warnings": []}
    for row in t["paths"]:
        role = (value(column(row, "role")) or "").lower()
        arch["paths"].append({
            "path": paths_of(column(row, "path")),
            "role": role,
            "profile": (value(column(row, "profile")) or None),
            "description": value(column(row, "description")) or "",
        })
    for row in t.get("oracles", []):
        arch["oracles"].append({
            "path": paths_of(column(row, "path")),
            "kind": (value(column(row, "kind")) or "").lower(),
            "command": value(column(row, "command")),
            "correspondence": paths_of(column(row, "correspondence", "correspondence table")),
            "guards": paths_of(column(row, "guards", "guard location", "guards location")),
        })
    for row in t.get("normative dependencies", []):
        arch["normative"].append({
            "document": paths_of(column(row, "document", "documents")),
            "normative": paths_of(column(row, "normative", "uses", "dependencies")),
        })
    for row in t.get("mapped pairs", []):
        arch["pairs"].append({
            "document": paths_of(column(row, "document", "statement")),
            "counterpart": paths_of(column(row, "counterpart", "formal counterpart")),
            "correspondence": paths_of(column(row, "correspondence", "correspondence table")),
        })
    return arch


def validate(arch, root):
    errors, warnings = [], arch["warnings"]
    known = sorted(p.stem for p in PROFILES_DIR.glob("*.md"))
    for e in arch["paths"]:
        name = ", ".join(e["path"]) or "(empty path)"
        if not e["path"]:
            errors.append("a row of Paths has no path")
        if e["role"] not in ROLES:
            errors.append(f"{name}: unknown role `{e['role']}` (one of {', '.join(ROLES)})")
        if e["role"] == "audited":
            if not e["profile"]:
                errors.append(f"{name}: audited, but no profile (`formal` is the only one so far)")
            elif e["profile"] not in known:
                warnings.append(f"{name}: profile `{e['profile']}` does not exist yet (existing: {', '.join(known)})")
        for p in e["path"]:
            if root and not any(c in p for c in "*?[") and not (root / p.rstrip("/")).exists():
                warnings.append(f"{p}: listed, but not found in the repository")
            if any_match(CONFIGURATION + AUDIT_RECORDS, p):
                errors.append(f"{p}: the architecture describes the project, not SpecAudit's own files")
    oracle_paths = [p for e in arch["paths"] if e["role"] == "oracle" for p in e["path"]]
    for o in arch["oracles"]:
        name = ", ".join(o["path"]) or "(empty path)"
        if not o["path"] or not all(any_match(oracle_paths, p) or p in oracle_paths for p in o["path"]):
            errors.append(f"oracle {name}: its path must have the role `oracle` in Paths")
        if o["kind"] not in ORACLE_KINDS:
            errors.append(f"oracle {name}: unknown kind `{o['kind']}` (one of {', '.join(ORACLE_KINDS)})")
        if not o["command"]:
            errors.append(f"oracle {name}: no command")
    for e in arch["paths"]:
        if e["role"] == "oracle" and not any(set(e["path"]) & set(o["path"]) for o in arch["oracles"]):
            warnings.append(f"{', '.join(e['path'])}: role `oracle` without a row in Oracles (no command: not an oracle)")
    audited = [p for e in arch["paths"] if e["role"] == "audited" for p in e["path"]]
    for pair in arch["pairs"]:
        name = ", ".join(pair["document"])
        if not pair["document"] or not pair["counterpart"]:
            errors.append(f"mapped pair {name or '(empty)'}: a document and a counterpart are required")
        for d in pair["document"]:
            if role_of(arch, d) != "audited":
                errors.append(f"mapped pair: {d} is not `audited`")
        for c in pair["counterpart"]:
            if not any_match(oracle_paths, c):
                warnings.append(f"mapped pair {name}: counterpart {c} is not inside an oracle")
    for n in arch["normative"]:
        for p in n["normative"]:
            r = role_of(arch, p)
            if r not in ("normative", None) and not matches(".specaudit/", p):
                warnings.append(f"normative dependency {p} has the role `{r}`")
    if not audited:
        errors.append("no path has the role `audited`: nothing to audit")
    return errors


def load(root):
    path = Path(root) / FILE
    if not path.exists():
        raise FileNotFoundError(str(path))
    arch = parse(path.read_text(encoding="utf-8"))
    arch["errors"] = validate(arch, Path(root))
    return arch


# --- Questions on the architecture -------------------------------------------------------------------------------

def role_of(arch, path):
    e = best(arch["paths"], path)
    return e["role"] if e else None


def deprecated_config(config):
    """The `profiles` and `normative` keys of an orchestrator configuration (deprecated: they belong in the
    architecture now). Only the simple forms the documentation shows are read: `"pattern": value` and `[a, b]`."""
    out = {"profiles": {}, "normative": {}}
    if not config or not Path(config).exists():
        return out
    text = Path(config).read_text(encoding="utf-8")
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return out
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"\S", line):
            key = line.split(":", 1)[0].strip()
            continue
        if key not in out:
            continue
        kv = re.match(r"\s+[\"']?(.+?)[\"']?\s*:\s*(.+?)\s*(#.*)?$", line)
        if not kv:
            continue
        v = kv.group(2).strip()
        if key == "normative":
            out[key][kv.group(1)] = [norm(x.strip(" \"'")) for x in v.strip("[]").split(",") if x.strip()]
        else:
            out[key][kv.group(1)] = v.strip("\"'")
    return out


def normative_for(arch, document, config=None):
    """The normative dependencies of a document: the rows of the table whose document covers it, otherwise every
    `normative` path; then the deprecated keys of the configuration, for one version."""
    rows = [n for n in arch["normative"] if any_match(n["document"], document)]
    if rows:
        deps = [p for n in rows for p in n["normative"]]
    else:
        deps = [p for e in arch["paths"] if e["role"] == "normative" for p in e["path"]]
    for pattern, extra in deprecated_config(config)["normative"].items():
        if matches(pattern, document) or glob_regex(pattern).match(document):
            deps += [p for p in extra if p not in deps]
    return deps


def writable(arch, path, changed, corpus=None):
    """(allowed, reason) for a change of `path`, the other changed paths being `changed`."""
    path = norm(path)
    own = list(AUDIT_RECORDS) + ([norm(corpus).rstrip("/") + "/"] if corpus else [])
    own += [g if g.endswith("/") or "." in g.rsplit("/", 1)[-1] else g + "/" for o in arch["oracles"] for g in o["guards"]]
    if any_match(CONFIGURATION, path):
        return False, "configuration (the architecture and the orchestrator's configuration are never changed by an audit)"
    if any_match(own, path):
        return True, "audit records, corpus or guards"
    role = role_of(arch, path)
    if role == "audited":
        return True, "audited"
    for pair in arch["pairs"]:
        if any_match(pair["counterpart"] + pair["correspondence"], path):
            docs = [c for c in changed if any_match(pair["document"], c)]
            if docs:
                return True, f"mapped counterpart, changed with {docs[0]}"
            return False, f"mapped counterpart of {', '.join(pair['document'])}, changed without its document"
    return False, role or "unlisted"


def readable(arch, path, agent):
    path = norm(path)
    role = role_of(arch, path)
    if role == "ignored":
        return False, "ignored by the architecture"
    if not agent:
        return True, ""
    if any_match(AUDIT_RECORDS, path):
        return False, "results of audits"
    if any_match(HISTORY, path):
        return False, "session history"
    if any_match((".specaudit.md", ".specaudit/"), path):
        allowed = [p for n in arch["normative"] for p in n["normative"]]
        allowed += [p for e in arch["paths"] if e["role"] == "normative" for p in e["path"]]
        return (True, "") if any_match(allowed, path) else (False, "audit configuration")
    if role in ("original", "prior-version"):
        return False, f"{role}: an earlier version of the document"
    return True, ""


def git_paths(root, *args):
    out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise ArchError(out.stderr.strip() or f"git {' '.join(args)} failed")
    return [norm(l) for l in out.stdout.splitlines() if l.strip()]


# --- Commands -----------------------------------------------------------------------------------------------------

def missing_message(root):
    return (f"No {FILE} at the root of {root}. SpecAudit audits a project only once its architecture is known: run "
            f"/spec-audit:init, which proposes it and writes it once you confirm (or write it by hand, format in "
            f"docs/usage.md), then launch the audit again.")


def cmd_require(a):
    try:
        arch = load(a.root)
    except FileNotFoundError:
        print(missing_message(a.root), file=sys.stderr)
        return 2
    except ArchError as e:
        print(f"{FILE} is not readable: {e}", file=sys.stderr)
        return 1
    for w in arch["warnings"]:
        print(f"warning: {w}")
    if arch["errors"]:
        for e in arch["errors"]:
            print(f"error: {e}", file=sys.stderr)
        return 1
    audited = [p for e in arch["paths"] if e["role"] == "audited" for p in e["path"]]
    print(f"{FILE}: {len(arch['paths'])} paths, audited: {', '.join(audited)}; {len(arch['oracles'])} oracle(s), "
          f"{len(arch['pairs'])} mapped pair(s)")
    return 0


def cmd_show(a):
    arch = load(a.root)
    arch["deprecated"] = deprecated_config(a.config)
    if arch["deprecated"]["profiles"] or arch["deprecated"]["normative"]:
        arch["warnings"].append(f"{a.config}: the keys `profiles` and `normative` are deprecated; they belong in {FILE}")
    if a.json:
        print(json.dumps(arch, ensure_ascii=False, indent=2))
    else:
        for e in arch["paths"]:
            print(f"{', '.join(e['path'])}\t{e['role']}\t{e['profile'] or '—'}")
        for o in arch["oracles"]:
            print(f"oracle {', '.join(o['path'])}\t{o['kind']}\t{o['command']}")
        for w in arch["warnings"]:
            print(f"warning: {w}")
        for e in arch["errors"]:
            print(f"error: {e}")
    return 1 if arch["errors"] else 0


def cmd_role(a):
    arch = load(a.root)
    for p in a.paths:
        print(f"{norm(p)}\t{role_of(arch, p) or 'unlisted'}")
    return 0


def cmd_normative(a):
    arch = load(a.root)
    for p in normative_for(arch, norm(a.document), a.config):
        print(p)
    return 0


def cmd_check(a):
    arch = load(a.root)
    if a.staged:
        changed = git_paths(a.root, "diff", "--cached", "--name-only", "--no-renames")
    elif a.since:
        changed = git_paths(a.root, "diff", "--name-only", "--no-renames", a.since)
        changed += [p for p in git_paths(a.root, "ls-files", "--others", "--exclude-standard") if p not in changed]
    else:
        changed = [norm(p) for p in a.paths]
    refused = []
    for p in changed:
        ok, why = writable(arch, p, changed, a.corpus)
        if not ok:
            refused.append((p, why))
    for p, why in refused:
        print(f"refused: {p} ({why})")
    if refused:
        print(f"{len(refused)} path(s) outside what the audit may change, per {FILE}: unstage and restore them, "
              f"and record the attempt in the register as an error of the audit", file=sys.stderr)
        return 1
    print(f"ok: {len(changed)} path(s), all allowed")
    return 0


def cmd_hook(a):
    """PreToolUse hook: refuse a write outside what the audit may change, and an agent's read of what it must not
    see. Never blocks on an error of its own."""
    try:
        event = json.load(sys.stdin)
        tool = event.get("tool_name", "")
        if tool not in WRITE_TOOLS + READ_TOOLS:
            return 0
        arch = load(a.root)
        inp = event.get("tool_input") or {}
        raw = inp.get("file_path") or inp.get("notebook_path") or inp.get("path")
        if not raw:
            return 0
        root = Path(a.root).resolve()
        target = Path(raw)
        if not target.is_absolute():
            target = Path(event.get("cwd") or root) / target
        try:
            rel = target.resolve().relative_to(root).as_posix()
        except ValueError:
            return 0  # outside the worktree: the scratch directories
        agent = bool(event.get("agent_id"))
        if tool in WRITE_TOOLS:
            if agent:
                ok, why = False, "agents change nothing in the project; write in your scratch directory"
            else:
                ok, why = writable(arch, rel, [], a.corpus)
                if not ok and why.startswith("mapped counterpart"):
                    ok = True  # the commit check holds the pairing; the counterpart may be edited first
        else:
            ok, why = readable(arch, rel, agent)
        if not ok:
            print(f"refused by {FILE}: {rel} ({why})", file=sys.stderr)
            return 2
    except Exception:
        return 0
    return 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")  # paths and descriptions are not ASCII; a Windows console is not UTF-8
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    def add(name, fn):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".")
        p.set_defaults(fn=fn)
        return p
    add("require", cmd_require)
    p = add("show", cmd_show); p.add_argument("--config"); p.add_argument("--json", action="store_true")
    p = add("role", cmd_role); p.add_argument("paths", nargs="+")
    p = add("normative", cmd_normative); p.add_argument("--config"); p.add_argument("document")
    p = add("check", cmd_check); p.add_argument("--corpus"); p.add_argument("--staged", action="store_true")
    p.add_argument("--since"); p.add_argument("paths", nargs="*")
    p = add("hook", cmd_hook); p.add_argument("--corpus")
    a = ap.parse_args(argv)
    a.root = Path(a.root)
    if getattr(a, "corpus", None) and Path(a.corpus).is_absolute():
        try:  # the register may record the corpus by its absolute path in the worktree
            a.corpus = Path(a.corpus).resolve().relative_to(a.root.resolve()).as_posix()
        except ValueError:
            pass
    try:
        return a.fn(a)
    except FileNotFoundError:
        print(missing_message(a.root), file=sys.stderr)
        return 2
    except ArchError as e:
        print(f"{FILE}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
