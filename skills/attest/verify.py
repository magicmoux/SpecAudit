#!/usr/bin/env python3
"""Check the attestation of each results folder listed in SPECAUDITS.md, and optionally record it in the index.

  python3 verify.py                 print the status of every folder of the index
  python3 verify.py --update        also write it in the index's "Attested" column

Run it from the root of the project. A folder SpecAudit-<stamp>/ is attested by a signed git tag
specaudit/SpecAudit-<stamp> on a commit that holds the folder. Its status is:

  yes: <signer>, <date>        the signature is valid here, and the folder is unchanged since the tagged commit
  changed since attestation    the signature is valid, but the folder differs now from what was signed
  signed, not verified here    the tag is signed, but this machine cannot check it (key or tool missing)
  invalid signature            the signature does not match
  unsigned tag                 the tag exists but carries no signature: it attests nothing
  no                           no tag

Only "yes" is an attestation. The exit code is 0 when every folder is attested, 1 otherwise, 2 on a malformed index.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

INDEX = Path("SPECAUDITS.md")
ROW = re.compile(r"^\|\s*\[(SpecAudit-[0-9]{8}_[0-9]{4}(?:-[0-9]+)?)\]")


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


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--update", action="store_true", help='write the status in the "Attested" column')
    args = parser.parse_args()
    if not INDEX.is_file():
        print("no SPECAUDITS.md here: run from the root of the project", file=sys.stderr)
        return 2

    lines = INDEX.read_text(encoding="utf-8").split("\n")
    header = next((i for i, line in enumerate(lines) if line.startswith("| Results folder")), None)
    if header is None:
        print("SPECAUDITS.md has no index table", file=sys.stderr)
        return 2
    columns = [c.strip() for c in lines[header].strip("|").split("|")]
    if "Attested" not in columns:
        print('the index has no "Attested" column', file=sys.stderr)
        return 2
    col = columns.index("Attested")

    all_attested, results = True, []
    for i, line in enumerate(lines):
        match = ROW.match(line)
        if not match:
            continue
        folder = match.group(1)
        state = status(folder)
        all_attested &= state.startswith("yes")
        results.append((folder, state))
        if args.update:
            cells = line.strip().strip("|").split("|")
            if len(cells) == len(columns):
                cells[col] = f" {state} "
                lines[i] = "|" + "|".join(cells) + "|"

    for folder, state in results:
        print(f"{folder}  {state}")
    if args.update:
        INDEX.write_text("\n".join(lines), encoding="utf-8")
    return 0 if all_attested else 1


if __name__ == "__main__":
    sys.exit(main())
