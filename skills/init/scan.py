#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Max Brönnimann <https://github.com/magicmoux>
# SPDX-License-Identifier: LicenseRef-PolyForm-Shield-1.0.0
"""Propose a project's architecture, SPECAUDIT_ARCH.md, from its files: the first step of /spec-audit:init.

  python3 scan.py [--root <repo>] [--json] [--diff]

Reads the files git tracks or would track (`git ls-files --cached --others --exclude-standard`, so nothing git
ignores), and of their content only what it needs: build files of mechanized developments (lakefile.toml or
lakefile.lean, lean-toolchain, _CoqProject, ROOT, *.agda-lib, pyproject.toml), the first lines of READMEs, the
markers of formal content in documents (Definition, Lemma, Theorem, Proof…), and markdown tables that look like a
correspondence between results and formal names. It writes nothing.

Output: the proposed SPECAUDIT_ARCH.md (default; the points to settle with the user on stderr), or the same as JSON
(--json), each entry with the evidence for it (`why`), and the points to settle (`questions`). With --diff, the changes against the existing
SPECAUDIT_ARCH.md instead: entries added, removed or changed.

The proposal is a starting point for the conversation with the user, who confirms or adjusts it: a heuristic reads
names and markers, not meaning.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "start" / "references"))
import arch as A  # noqa: E402  (the parser and the format live with the audit, which reads the file)

DOC_EXT = {".md", ".tex", ".typ", ".rst", ".adoc", ".org", ".txt"}
BIB_EXT = {".bib", ".pdf", ".ris", ".djvu", ".ps", ".enw"}
NEUTRAL = re.compile(r"^(readme|license|licence|changelog|contributing|authors|notice|copying)(\..*)?$", re.I)
FORMAL = re.compile(r"\*\*(definition|lemma|theorem|proposition|corollary)\b|\\begin\{(theorem|lemma|definition|proof)\}"
                    r"|^#+.*\b(theorem|lemma|proof)\b|\*proof\.\*", re.I | re.M)
F_SOURCES = re.compile(r"^(references?|refs|biblio\w*|bibliography|literature|papers|citations|cited)$", re.I)
F_ORIGINAL = re.compile(r"^(source|original|originals?|orig|submitted|submission)$", re.I)
F_PRIOR = re.compile(r"^(archive[sd]?|old|previous|prior|versions?|history|v\d+)$", re.I)
F_NORMATIVE = re.compile(r"^(normative|standards?|glossary|notations?)$", re.I)
N_NORMATIVE = re.compile(r"(notation|glossary|definitions|conventions|standard|normative|style[-_ ]?guide)", re.I)
N_ORIGINAL = re.compile(r"(^|[-_. ])(original|orig|submitted)([-_. ]|$)", re.I)
N_REVISED = re.compile(r"(^|[-_. ])(revised|revision[-_ ]?\d*|rev\d*|v(\d+)|final|camera[-_ ]?ready)([-_. ]|$)", re.I)
HISTORY = (".forge/", ".claude/")
SELF = ("SPECAUDITS.md", "SpecAudit-*/", "spec-audit/", ".specaudit.md", ".specaudit/", A.FILE, "spec-guards/")
CORR_HEADER = re.compile(r"(lean|coq|rocq|isabelle|agda|formal|mechani[sz]|isar)", re.I)
CORR_RESULT = re.compile(r"(result|theorem|lemma|statement|paper|document|definition)", re.I)


def files_of(root):
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
        tracked = set(subprocess.run(["git", "-C", str(root), "ls-files", "--cached"], capture_output=True, text=True,
                                     encoding="utf-8", check=True).stdout.splitlines())
        files = sorted(set(out.splitlines()))
    except (subprocess.CalledProcessError, FileNotFoundError):
        files = sorted(p.relative_to(root).as_posix() for p in Path(root).rglob("*") if p.is_file() and ".git" not in p.parts)
        tracked = set(files)
    return [f for f in files if f], tracked


def read(root, rel, limit=200_000):
    try:
        p = Path(root) / rel
        if p.stat().st_size > limit:
            return p.open(encoding="utf-8", errors="replace").read(limit)
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def parent(rel):
    return rel.rsplit("/", 1)[0] if "/" in rel else ""


def segments(rel):
    return rel.split("/")[:-1]


# --- Oracles ------------------------------------------------------------------------------------------------------

def lean_libs(text, toml):
    if toml:
        libs = []
        for block in re.split(r"\n(?=\[\[)", text):
            if block.lstrip().startswith("[[lean_lib]]"):
                name = re.search(r'^\s*name\s*=\s*"([^"]+)"', block, re.M)
                globs = re.findall(r'"([^"]+)"', (re.search(r"^\s*globs\s*=\s*\[(.*?)\]", block, re.M | re.S) or [None, ""])[1])
                if name:
                    libs.append((name.group(1), globs))
        return libs
    return [(m.group(1).strip("«»"), re.findall(r"`([\w.]+)", m.group(2) or ""))
            for m in re.finditer(r"lean_lib\s+(«[^»]+»|\S+)(?:\s+where([\s\S]*?)(?=\n\S|\Z))?", text)]


def find_oracles(root, files):
    oracles, by_dir = [], {}
    for f in files:
        by_dir.setdefault(parent(f), set()).add(f.rsplit("/", 1)[-1])
    for d, names in sorted(by_dir.items()):
        pre = f"{d}/" if d else ""
        flag = f" -d {d}" if d else ""
        if names & {"lakefile.toml", "lakefile.lean", "lean-toolchain"}:
            toml = "lakefile.toml" in names
            text = read(root, pre + ("lakefile.toml" if toml else "lakefile.lean"))
            libs = lean_libs(text, toml)
            guard_lib = next((n for n, g in libs if "guard" in n.lower() or any("guard" in x.lower() for x in g)), None)
            counterpart = [x for n, _ in libs if n != guard_lib for x in (f"{pre}{n}/", f"{pre}{n}.lean")
                           if any(ff == x or ff.startswith(x) for ff in files)]
            questions = []
            if guard_lib:
                guards = f"{pre}{guard_lib}/"
            else:
                first = next((n for n, _ in libs), "Guards")
                guards = f"{pre}{first}/Guards/"
                questions.append(f"{guards}: the build compiles a guard module only if a library's globs cover it or "
                                 f"an imported module imports it; adjust the lakefile, or name another location")
            oracles.append({"path": pre or "./", "kind": "formal", "command": f"lake{flag} build", "guards": [guards],
                            "counterpart": counterpart, "tool": "Lean", "questions": questions,
                            "why": "Lean development: " + ", ".join(sorted(names & {"lakefile.toml", "lakefile.lean", "lean-toolchain"}))})
        elif "_CoqProject" in names or "_RocqProject" in names:
            oracles.append({"path": pre or "./", "kind": "formal", "command": f"make -C {d or '.'}", "guards": [f"{pre}Guards/"],
                            "counterpart": [], "tool": "Coq", "why": "Coq development: _CoqProject",
                            "questions": [f"{pre}: confirm the build command"]})
        elif "ROOT" in names and any(n.endswith(".thy") for n in names):
            oracles.append({"path": pre or "./", "kind": "formal", "command": f"isabelle build -D {d or '.'}",
                            "guards": [f"{pre}Guards/"], "counterpart": [], "tool": "Isabelle", "why": "Isabelle session: ROOT",
                            "questions": []})
        elif any(n.endswith(".agda-lib") for n in names):
            oracles.append({"path": pre or "./", "kind": "formal", "command": "agda <main module>", "guards": [f"{pre}Guards/"],
                            "counterpart": [], "tool": "Agda", "why": "Agda library: *.agda-lib",
                            "questions": [f"{pre}: give the Agda command that checks the development"]})
    # A test runner: a folder of test_*.py, or pytest configured.
    tests = sorted({parent(f) for f in files if re.match(r"(.*/)?test_[^/]*\.py$", f) and not any(A.matches(s, f) for s in SELF)})
    tests = [t for t in tests if not any(A.matches(o["path"], t + "/") for o in oracles)]
    roots = [t for t in tests if not any(t != u and t.startswith(u + "/") for u in tests)]
    for t in roots:
        oracles.append({"path": f"{t}/" if t else "./", "kind": "runner", "command": f"python -m pytest {t or '.'}",
                        "guards": [], "counterpart": [], "tool": "pytest", "why": "test files test_*.py",
                        "questions": [f"{t or '.'}: confirm that `python -m pytest {t or '.'}` runs here"]})
    return oracles


def correspondence_tables(root, files):
    """Files holding a markdown table from results to formal names: header naming a prover or "formal", and a result."""
    found = []
    for f in files:
        if Path(f).suffix.lower() not in {".md", ".txt", ".rst"}:
            continue
        text = read(root, f)
        for line in text.splitlines():
            row = A.cells(line)
            if row and len(row) >= 2 and any(CORR_HEADER.search(c) for c in row) and any(CORR_RESULT.search(c) for c in row):
                found.append(f)
                break
    return found


# --- Documents ----------------------------------------------------------------------------------------------------

def classify(root, f, oracles):
    """(role, profile, why) of one file, or None for a file the architecture need not list."""
    name = f.rsplit("/", 1)[-1]
    ext = Path(f).suffix.lower()
    segs = segments(f)
    if any(A.matches(h, f) for h in HISTORY):
        return ("ignored", None, "session history")
    if NEUTRAL.match(name):
        return None
    if any(F_SOURCES.match(s) for s in segs) or ext in BIB_EXT:
        return ("sources", None, "bibliographic material" if ext in BIB_EXT else f"in a `{next(s for s in segs if F_SOURCES.match(s))}/` folder")
    if any(F_NORMATIVE.match(s) for s in segs) or (ext in DOC_EXT and N_NORMATIVE.search(Path(name).stem)):
        return ("normative", None, "notation, glossary or standard")
    if ext not in DOC_EXT:
        return None
    text = read(root, f)
    formal = bool(FORMAL.search(text))
    if any(F_ORIGINAL.match(s) for s in segs) or N_ORIGINAL.search(Path(name).stem):
        return ("original", None, "in a folder or under a name for the original version")
    if any(F_PRIOR.match(s) for s in segs):
        return ("prior-version", None, "in a folder for earlier versions")
    if formal:
        return ("audited", "formal", "definitions, statements and proofs")
    return ("unclassified", None, "a document without formal statements")


def revision_groups(entries):
    """Two documents of the same name but for a revision mark: the revised one is audited, the other prior-version."""
    stems = {}
    for f, e in entries.items():
        if e and e[0] == "audited":
            base = N_REVISED.sub("", Path(f).stem).strip("-_. ").lower()
            stems.setdefault((parent(f), base), []).append(f)
    for group in stems.values():
        if len(group) < 2:
            continue
        def rank(f):
            m = N_REVISED.search(Path(f).stem)
            return (bool(m), int(m.group(4)) if m and m.group(4) else 0)
        latest = max(group, key=rank)
        for f in group:
            if f != latest:
                entries[f] = ("prior-version", None, f"an earlier version of {latest}")


def compress(entries, files):
    """One entry per folder whose listed files all have the same role and profile; otherwise its files or subfolders."""
    out = []

    def walk(d):
        pre = f"{d}/" if d else ""
        inside = {f: e for f, e in entries.items() if f.startswith(pre)}
        keys = {(e[0], e[1]) for e in inside.values() if e}
        if d and len(keys) == 1:
            role, profile = keys.pop()
            whys = sorted({e[2] for e in inside.values() if e})
            out.append({"path": [pre], "role": role, "profile": profile, "why": "; ".join(whys),
                        "files": sorted(f for f, e in inside.items() if e)})
            return
        here = sorted(f for f in inside if parent(f) == d and inside[f])
        for f in here:
            role, profile, why = inside[f]
            out.append({"path": [f], "role": role, "profile": profile, "why": why, "files": [f]})
        for sub in sorted({f[len(pre):].split("/", 1)[0] for f in inside if "/" in f[len(pre):]}):
            walk(pre + sub)

    walk("")
    return out


def describe(entry, readme_lines):
    files = entry["files"]
    role = entry["role"]
    folder = entry["path"][0].endswith("/")
    readme = readme_lines.get(entry["path"][0].rstrip("/"))
    if readme:
        return readme
    n = f"{len(files)} files" if len(files) > 1 else files[0].rsplit("/", 1)[-1]
    return {
        "audited": f"documents with definitions, statements and proofs ({n})" if folder else "document with definitions, statements and proofs",
        "original": "the original version" + (f" ({n})" if folder else ""),
        "prior-version": entry["why"],
        "normative": "definitions and notation used by the documents",
        "sources": f"references and bibliographic material ({n})",
        "ignored": "session history",
        "unclassified": "documents without formal statements",
    }.get(role, "")


def readme_descriptions(root, files):
    """A folder's README, by its first sentence that is not a heading: what the project says the folder is."""
    out = {}
    root_readme = next((f for f in files if "/" not in f and NEUTRAL.match(f) and f.lower().startswith("readme")), None)
    if root_readme:
        for line in read(root, root_readme).splitlines():
            m = re.match(r"\s*[-*]\s+`([^`]+?)/?`\s*[:—–-]\s*(.+)", line)
            if m:
                out[m.group(1).strip("/")] = m.group(2).strip().rstrip(".")
    return out


# --- The proposal -------------------------------------------------------------------------------------------------

def propose(root):
    root = Path(root)
    files, tracked = files_of(root)
    files = [f for f in files if not any(A.matches(s, f) for s in SELF)]
    oracles = find_oracles(root, files)
    questions = []
    entries = {}
    for f in files:
        if any(A.matches(o["path"], f) for o in oracles if o["kind"] == "formal" or o["path"] != "./"):
            continue
        entries[f] = classify(root, f, oracles)
    revision_groups(entries)
    paths = compress({f: e for f, e in entries.items() if e}, files)
    readmes = readme_descriptions(root, files)
    for e in paths:
        e["description"] = describe(e, readmes)
    for o in oracles:
        paths.append({"path": [o["path"]], "role": "oracle", "profile": None, "why": o["why"],
                      "description": readmes.get(o["path"].strip("/")) or f"{o['tool']} {'development' if o['kind'] == 'formal' else 'tests'}",
                      "files": []})
        questions += o["questions"]
    unclassified = [e for e in paths if e["role"] == "unclassified"]
    for e in unclassified:
        questions.append(f"{e['path'][0]}: no formal statement found; `formal` is the only profile so far, and suits "
                         f"other documents poorly: audited with `formal`, or left out (read-only)?")
    paths = [e for e in paths if e["role"] != "unclassified"]
    order = {r: i for i, r in enumerate(A.ROLES)}
    paths.sort(key=lambda e: (order.get(e["role"], 99), e["path"][0]))

    # Correspondence tables and mapped pairs.
    tables = correspondence_tables(root, files)
    audited_docs = [f for e in paths if e["role"] == "audited" for f in e["files"]]
    pairs = []
    for o in oracles:
        o["correspondence"] = [t for t in tables if A.matches(o["path"], t)] if o["path"] != "./" else tables
        if o["kind"] != "formal":
            continue
        if not o["correspondence"]:
            o["correspondence"] = [t for t in tables if t in audited_docs]
        for t in o["correspondence"]:
            text = read(root, t)
            named = [d for d in audited_docs if d in text or (d.rsplit("/", 1)[-1] in text and d != t)]
            if t in audited_docs:
                named = [t]
            if not named and len(audited_docs) == 1:
                named = audited_docs
            if named:
                pairs.append({"document": named, "counterpart": o["counterpart"] or [o["path"]], "correspondence": [t]})
            else:
                questions.append(f"{t}: which audited documents does this correspondence table map?")
        if not o["correspondence"]:
            questions.append(f"{o['path']}: no correspondence table found between the documents' results and "
                             f"{o['tool']} names; without one, the audit cannot use the development as a formal oracle")

    # Normative dependencies: the normative documents each audited document names.
    normative_paths = [p for e in paths if e["role"] == "normative" for p in e["path"]]
    normative_files = [f for e in paths if e["role"] == "normative" for f in e["files"]]
    norm_rows = []
    if normative_paths and len({d for d in audited_docs}) > 1:
        for d in audited_docs:
            text = read(root, d)
            used = [n for n in normative_files if n.rsplit("/", 1)[-1] in text]
            if used:
                norm_rows.append({"document": [d], "normative": used})

    # The keys of the orchestrator's configuration that belong in the architecture now.
    config = next((c for c in (".specaudit/config.md", ".specaudit.md") if (root / c).exists()), None)
    moved = A.deprecated_config(root / config) if config else {"profiles": {}, "normative": {}}
    for pattern, profile in moved["profiles"].items():
        hit = [e for e in paths if e["role"] == "audited" and any(A.matches(pattern, f) or A.glob_regex(pattern).match(f) for f in e["files"])]
        if hit:
            for e in hit:
                e["profile"] = profile
        else:
            paths.append({"path": [pattern], "role": "audited", "profile": profile, "why": f"`profiles` of {config}",
                          "description": "", "files": []})
    for pattern, deps in moved["normative"].items():
        norm_rows.append({"document": [pattern], "normative": deps})
    if moved["profiles"] or moved["normative"]:
        questions.append(f"{config}: its keys `profiles` and `normative` are taken into the proposal; once "
                         f"{A.FILE} is written, remove them from {config} (they are deprecated there)")

    untracked = sorted(f for e in paths for f in e["files"] if f not in tracked)
    if untracked:
        questions.append("not tracked by git, hence absent from an audit's worktree: " + ", ".join(untracked))
    return {
        "paths": [{k: e[k] for k in ("path", "role", "profile", "description", "why")} for e in paths],
        "oracles": [{k: o[k] for k in ("path", "kind", "command", "correspondence", "guards", "why")} for o in oracles],
        "normative": norm_rows,
        "pairs": pairs,
        "questions": questions,
    }


# --- Rendering ----------------------------------------------------------------------------------------------------

HEADER = f"""# SpecAudit architecture

The layout of this repository and the role of each part, as SpecAudit reads it. `/spec-audit:init` proposed it; it may be edited by hand, and `/spec-audit:init` run again proposes changes to it. It describes only what anyone can see in the repository and says nothing about any audit: scope, focus and notes for the orchestrator belong in `.specaudit.md` or `.specaudit/config.md`.

Format: the four tables below, under these headings; `—` means none. A path is relative to the root of the repository: `dir/` is a folder and everything in it, `*` matches within one segment of a path and `**` across segments, and when several rows match a path the most specific one holds. A cell may list several paths, separated by commas.

- **Paths.** `Role` is one of: `audited`, the documents to check, which an audit may fix; `original` and `prior-version`, earlier versions, read-only; `normative`, documents whose definitions the audited ones use; `sources`, references and bibliographic material, frozen; `oracle`, a verification artifact (see Oracles); `ignored`, neither read nor changed. `Profile`, for an audited path: `formal` (theory, proofs, algorithms, formal specifications), the only profile so far. A path not listed is read-only.
- **Oracles.** For each `oracle` path: its kind (`formal` for a mechanized development, `model` for a reference model or checker, `runner` for a test runner), the command that runs it from the root, the correspondence table between the documents' results and its names, and where new guard modules go (a place its command builds).
- **Normative dependencies.** The normative documents each audited document uses. Without a row for a document, it gets every `normative` path.
- **Mapped pairs.** An audited document and its formal counterpart, which must change together, with the correspondence table between them.
"""


def code(paths):
    return ", ".join(f"`{p}`" for p in paths) if paths else "—"


def render(p):
    out = [HEADER, "## Paths", "", "| Path | Role | Profile | Description |", "|---|---|---|---|"]
    for e in p["paths"]:
        out.append(f"| {code(e['path'])} | {e['role']} | {e['profile'] or '—'} | {e['description'] or '—'} |")
    out += ["", "## Oracles", "", "| Path | Kind | Command | Correspondence | Guards |", "|---|---|---|---|---|"]
    for o in p["oracles"]:
        out.append(f"| {code([o['path']] if isinstance(o['path'], str) else o['path'])} | {o['kind']} | `{o['command']}` | "
                   f"{code(o['correspondence'])} | {code(o['guards'])} |")
    out += ["", "## Normative dependencies", "", "| Document | Normative |", "|---|---|"]
    for n in p["normative"]:
        out.append(f"| {code(n['document'])} | {code(n['normative'])} |")
    out += ["", "## Mapped pairs", "", "| Document | Counterpart | Correspondence |", "|---|---|---|"]
    for m in p["pairs"]:
        out.append(f"| {code(m['document'])} | {code(m['counterpart'])} | {code(m['correspondence'])} |")
    return "\n".join(out) + "\n"


def diff(root, p):
    """The proposal against the existing file: what an update would change, row by row."""
    try:
        old = A.parse((Path(root) / A.FILE).read_text(encoding="utf-8"))
    except (OSError, A.ArchError) as e:
        return [f"no readable {A.FILE} to compare with ({e})"]
    lines = []
    def rp(e):
        return f"{e['role']} {e['profile']}" if e["profile"] else e["role"]
    def key(e):
        return ", ".join(e["path"])
    o_paths = {key(e): e for e in old["paths"]}
    n_paths = {key(e): e for e in p["paths"]}
    for k in n_paths:
        if k not in o_paths:
            lines.append(f"+ path {k}: {rp(n_paths[k])}")
        elif (o_paths[k]["role"], o_paths[k]["profile"]) != (n_paths[k]["role"], n_paths[k]["profile"]):
            lines.append(f"~ path {k}: {rp(o_paths[k])} → {rp(n_paths[k])}")
    for k in o_paths:
        if k not in n_paths:
            lines.append(f"- path {k}: {o_paths[k]['role']} (not proposed; kept if you wrote it on purpose)")
    o_or = {key(o): o for o in old["oracles"]}
    for o in p["oracles"]:
        k = o["path"]
        if k not in o_or:
            lines.append(f"+ oracle {k}: {o['kind']} `{o['command']}`")
        elif (o_or[k]["command"], o_or[k]["guards"], o_or[k]["correspondence"]) != (o["command"], o["guards"], o["correspondence"]):
            lines.append(f"~ oracle {k}: `{o_or[k]['command']}` → `{o['command']}`, guards {code(o_or[k]['guards'])} → "
                         f"{code(o['guards'])}, correspondence {code(o_or[k]['correspondence'])} → {code(o['correspondence'])}")
    for k in o_or:
        if k not in {o["path"] for o in p["oracles"]}:
            lines.append(f"- oracle {k} (not proposed)")
    o_pairs = {(key({"path": m["document"]}), key({"path": m["counterpart"]})) for m in old["pairs"]}
    for m in p["pairs"]:
        if (key({"path": m["document"]}), key({"path": m["counterpart"]})) not in o_pairs:
            lines.append(f"+ mapped pair {code(m['document'])} ↔ {code(m['counterpart'])}")
    return lines or ["no change"]


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")  # paths and descriptions are not ASCII; a Windows console is not UTF-8
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--diff", action="store_true")
    a = ap.parse_args(argv)
    p = propose(a.root)
    if a.json:
        print(json.dumps(p, ensure_ascii=False, indent=2))
    elif a.diff:
        print("\n".join(diff(a.root, p)))
    else:
        sys.stdout.write(render(p))
        for q in p["questions"]:  # on stderr, so that stdout is the file as it would be written
            print(f"to settle: {q}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
