---
description: Checks which spec-audit results folders are attested by a signed git tag, records it in the index SPECAUDITS.md, and gives the exact command to attest the others from the user's own machine. Never signs anything itself.
disable-model-invocation: true
argument-hint: "[<SpecAudit-folder> | <stamp> | <audited source> | --all] [--update]"
---

# Attest audit results

An audit records who launched it, but that is the git identity of the session, which anyone can set and which a cloud or automated session fills with a bot's. An attestation is something else: a person states, after reading the report, that they stand by the result, with an identity that a third party can check. Here it is a signed git tag `specaudit/<folder>` on the commit that holds the results folder: the signature ties the folder's exact content to a key the person controls, and anyone can verify it later with git.

That is why you never sign: the key must be the user's, and it must not be in this session. In a cloud session it is not even possible to sign in their name: such environments can replace git's signing program with their own, so a `git tag -s` run here would carry the environment's signature, not the user's.

1. **Choose the folder.** An attestation is about one result, so name it rather than guess it. From `$ARGUMENTS`, in this order:
   - a folder (`SpecAudit-20261010_2102`, its path, or its stamp `20261010_2102`), or an audited source as the index writes it (`selection.md`, `docs/spec/`), which means the newest folder of that source: pass it to `verify.py`, which resolves it and says when a source has older folders too. A target that matches nothing is an error, and `verify.py` lists the known folders: never pick the closest one;
   - `--all`: every folder of the index;
   - nothing: run `python3 "${CLAUDE_SKILL_DIR}/verify.py" --pending`. If it lists exactly one folder, take it and name it in your answer; if it lists several, ask which with AskUserQuestion (header "Attest", one option per folder with its audited source and outcome from the index, newest first), or, when no question can be asked, report them all and stop; if none, say that every folder is attested.
   Do not infer the folder from the current directory: in a Claude session the shell's directory returns to the project root after each command, so it says nothing about which result the user means.

2. **Check.** From the root of the project, run `python3 "${CLAUDE_SKILL_DIR}/verify.py" <folder>` (no folder with `--all`; add `--update` if `$ARGUMENTS` contains it). It prints one status per folder:
   - `yes: <signer>, <date>`: the signature is valid on this machine, and the folder is unchanged since the signed commit;
   - `changed since attestation`: validly signed, but the folder differs now from what was signed; the attestation no longer covers it;
   - `signed, not verified here`: the tag is signed, but this machine cannot check it (the signer's key is not trusted here, or the tool is missing); say how to check it where the key is known, and do not present it as attested;
   - `invalid signature`, `unsigned tag`, `no`: not attested.

3. **Explain how to attest** each folder checked that is not attested, with the exact commands for the user to run **on their own machine**, after reading the folder's report:

   ```bash
   git fetch                                   # if the results came from a cloud session
   F=SpecAudit-<YYYYmmdd_HHmm>
   git tag -s "specaudit/$F" "$(git log -1 --format=%H -- "$F")" -m "Attest $F: report read; <decision>"
   git push origin "specaudit/$F"              # so that others can verify it
   ```

   `git log -1 -- "$F"` finds the last commit that changed the folder, so the tag covers its final content. Signing needs a GPG or SSH key set up in git (`user.signingkey`, and `gpg.format ssh` for an SSH key), or Sigstore's `gitsign` for keyless signing tied to an e-mail through an OIDC login. GitHub shows a signed tag as "Verified" when the key is registered on the account.

4. **Record**, only with `--update`: `verify.py` rewrites the "Attested" column of the index, and nothing else. This is the one column a later command changes, because it records an event that comes after the closing; every other cell of a row stays as the closing wrote it. Commit only the index (`git add -- SPECAUDITS.md` then `git commit -m "spec-audit: attestation status" -- SPECAUDITS.md`), never push, and say what changed.

Never create, move, delete or sign a tag, and never mark a folder attested by editing the index by hand: the column must say only what `verify.py` can check.
