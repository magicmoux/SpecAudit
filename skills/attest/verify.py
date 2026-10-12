#!/usr/bin/env python3
"""Check the attestation of each results folder listed in SPECAUDITS.md, and optionally record it in the index.

  python3 verify.py                 print the status of every folder of the index
  python3 verify.py <target>...     only these folders; a target is a folder name (SpecAudit-20261010_210233), its path,
                                    its stamp (20261010_210233), or an audited source as the index writes it
                                    (selection.md, docs/spec/), which means the newest folder of that source
  python3 verify.py --pending       only the folders not attested, one name per line (to choose a target)
  python3 verify.py --update        also write the status in the "Attested" cell of each audit's section

Run it from the root of the project. Every audit has a section "## SpecAudit-<stamp>" in SPECAUDITS.md; only those that
left a results folder can be attested. A folder SpecAudit-<stamp>/ (stamp YYYYmmdd_HHmmss) is attested by a signed git tag
specaudit/SpecAudit-<stamp> on a commit that holds the folder. Its status is:

  yes: <signer>, <date>        the signature is valid here, and the folder is unchanged since the tagged commit
  changed since attestation    the signature is valid, but the folder differs now from what was signed
  signed, not verified here    the tag is signed, but this machine cannot check it (key or tool missing)
  invalid signature            the signature does not match
  unsigned tag                 the tag exists but carries no signature: it attests nothing
  no                           no tag

Only "yes" is an attestation. The exit code is 0 when every folder checked is attested, 1 otherwise, 2 on a malformed
index or a target that matches no folder (the known folders are then listed: a target is never approximated).
"""
import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

INDEX = Path("SPECAUDITS.md")
SECTION = re.compile(r"^## (SpecAudit-[0-9]{8}_[0-9]{6}(?:-[0-9]+)?)\s*$")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def status(folder):
    tag = f"specaudit/{folder}"
    if git("rev-parse", "-q", "--verify", f"refs/tags/{tag}").returncode != 0:
        return "no"
    if git("cat-file", "-t", tag).stdout.strip() != "tag":
        return "unsigned tag"  # a lightweight tag has no message, hence no signature
    body = git("cat-file", "tag", tag).stdout
    if "-----BEGIN" not in body:
        return "unsigned tag"
    check = git("tag", "-v", tag)
    report = check.stdout + check.stderr
    if check.returncode != 0:
        if re.search(r"BAD signature|Bad signature|could not verify|Signature verification failed", report, re.I) \
                and not re.search(r"No public key|no signing key|allowedSignersFile|gpg.ssh.allowedSignersFile|"
                                  r"cannot run|not found", report, re.I):
            return "invalid signature"
        return "signed, not verified here"
    signed = git("rev-parse", f"{tag}^{{commit}}:{folder}").stdout.strip()
    current = git("rev-parse", f"HEAD:{folder}").stdout.strip()
    if not signed or signed != current:
        return "changed since attestation"
    signer = re.search(r'(?:Good signature from|Good "git" signature for)\s+"?([^"\n]+?)"?(?:\s+with|\s*$|\s*\[)',
                       report, re.M)
    date = git("for-each-ref", "--format=%(taggerdate:short)", f"refs/tags/{tag}").stdout.strip()
    return f"yes: {signer.group(1).strip() if signer else 'valid signature'}, {date}"


def write_attested(states):
    """Write each folder's "Attested" cell, and nothing else, under the index lock of the start skill
    (references/register.md, "Writing the index"): the file is read again under the lock, so that an entry another
    audit wrote while the tags were being verified is kept."""
    lock = INDEX.with_name(INDEX.name + ".lock")  # an empty folder: git never tracks it
    for _ in range(120):
        try:
            os.mkdir(lock)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 600:  # older than ten minutes: its holder died
                    os.rmdir(lock)
                    continue
            except FileNotFoundError:
                continue  # released meanwhile
            time.sleep(1)
    else:
        print(f"SPECAUDITS.md is locked by another audit ({lock}); nothing written", file=sys.stderr)
        return False
    try:
        lines = INDEX.read_text(encoding="utf-8").split("\n")
        current = None
        for i, line in enumerate(lines):
            heading = SECTION.match(line)
            if heading:
                current = heading.group(1)
            elif line.startswith("## ") or line.startswith("# "):
                current = None
            elif current in states and re.match(r"^\|\s*Attested\s*\|", line):
                lines[i] = f"| Attested | {states[current]} |"
        INDEX.write_text("\n".join(lines), encoding="utf-8")
        return True
    finally:
        os.rmdir(lock)


def resolve(target, rows):
    """Folder names for one target, newest first; rows is [(folder, audited source)] in index order (newest first)."""
    name = target.rstrip("/\\").replace("\\", "/").split("/")[-1]
    for folder, _ in rows:
        if name in (folder, folder.removeprefix("SpecAudit-")):
            return [folder]
    source = target.strip().strip("`").replace("\\", "/").removeprefix("./")
    return [folder for folder, audited in rows
            if audited.strip("`").split(" (")[0].removeprefix("./") in (source, source.rstrip("/") + "/", source.rstrip("/"))]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("targets", nargs="*", help="folders to check (default: all)")
    parser.add_argument("--pending", action="store_true", help="list the folders not attested, one per line")
    parser.add_argument("--update", action="store_true", help='write the status in each section\'s "Attested" cell')
    args = parser.parse_args()
    if not INDEX.is_file():
        print("no SPECAUDITS.md here: run from the root of the project", file=sys.stderr)
        return 2

    lines = INDEX.read_text(encoding="utf-8").split("\n")
    # One section per audit, "## SpecAudit-<stamp>", newest first, with a two-column table: the audited object, the
    # results folder (a link, or "none…" for an audit that left none), and the "Attested" cell this script maintains.
    entries, current = [], None
    for i, line in enumerate(lines):
        heading = SECTION.match(line)
        if heading:
            current = {"id": heading.group(1), "audited": "", "folder": False, "attested": None}
            entries.append(current)
            continue
        if line.startswith("## ") or line.startswith("# "):
            current = None
            continue
        if current is None or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        if cells[0] == "Audited object":
            current["audited"] = cells[1]
        elif cells[0] == "Results folder":
            current["folder"] = f"]({current['id']}/" in cells[1] or cells[1].startswith(f"[{current['id']}")
        elif cells[0] == "Attested":
            current["attested"] = i
    if not entries:
        print("SPECAUDITS.md has no audit section (## SpecAudit-<stamp>)", file=sys.stderr)
        return 2
    rows = [(e["id"], e["audited"]) for e in entries if e["folder"]]

    wanted = None
    if args.targets:
        wanted = set()
        for target in args.targets:
            found = resolve(target, rows)
            if not found:
                print(f"no results folder matches {target!r}; the index lists:", file=sys.stderr)
                for folder, audited in rows:
                    print(f"  {folder}  {audited}", file=sys.stderr)
                return 2
            if len(found) > 1:
                print(f"{target}: newest of {len(found)} folders for this source ({', '.join(found[1:])} are older)",
                      file=sys.stderr)
            wanted.add(found[0])

    all_attested, results = True, []
    for entry in entries:
        if not entry["folder"] or (wanted is not None and entry["id"] not in wanted):
            continue  # an audit that left no results folder has nothing to attest
        state = status(entry["id"])
        all_attested &= state.startswith("yes")
        results.append((entry["id"], state))
    if wanted is None and not results:
        print("no audit of the index has a results folder yet", file=sys.stderr)

    for folder, state in results:
        if args.pending:
            if not state.startswith("yes"):
                print(folder)
        else:
            print(f"{folder}  {state}")
    if args.update and results and not write_attested(dict(results)):
        return 2
    return 0 if all_attested else 1


if __name__ == "__main__":
    sys.exit(main())
