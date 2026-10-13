---
description: Detects the architecture of the project for SpecAudit (which paths are audited, original or earlier versions, normative, sources, oracles with their commands, ignored; the profile of each audited document; the pairs that change together), proposes it, and writes SPECAUDIT_ARCH.md at the root once the user confirms. /spec-audit:start refuses to run without that file. Run again, proposes changes to the existing file.
disable-model-invocation: true
argument-hint: "[<path to focus on>]"
---

# Initialize the project's architecture

`/spec-audit:start` audits a project only along its architecture: which documents it checks and may fix, which ones are earlier versions, normative references or sources it must leave alone, which verification artifacts can decide a statement, and where its guards go. This skill writes that architecture, `SPECAUDIT_ARCH.md` at the root of the repository, so that no audit runs on a guessed structure, and so that the user can read, correct and review it like any other file.

**What the file may hold.** Reviewers and adjudicators may read `SPECAUDIT_ARCH.md`: it says only what a referee could see in the repository, the layout and the role of each part. Never write in it anything about audits: no scope, no focus, no result not to change, no note for the orchestrator, no mention of earlier audits, errors or fixes. If the user gives such a note, it belongs in the orchestrator's configuration (`.specaudit.md` or `.specaudit/config.md`, docs/usage.md, "Project configuration"): offer to put it there instead.

Write nothing but `SPECAUDIT_ARCH.md`, and nothing at all before the user has confirmed (step 3).

1. **Scan.** From the root of the repository (`git rev-parse --show-toplevel`; outside a git repository, say that an audit needs one and stop), run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scan.py" --root "<root>" --json
   ```

   (`python` where `python3` does not print a Python 3 version, as on Windows where it can be the Microsoft Store stub). It lists the files git tracks or would track, nothing git ignores, and reads only what it needs: build files of mechanized developments, READMEs, the markers of formal content in documents, and tables that look like a correspondence between results and formal names. Its JSON gives each path with a role and the evidence for it (`why`), the oracles, the mapped pairs, and the `questions` it could not settle. If `$ARGUMENTS` names a path, look at it first and say what you found there.

   Then check the proposal yourself, reading only what a doubt requires: a folder's README, the head of a document whose role is unclear, the build file of an oracle, the correspondence table (does it map the audited document's results to formal names, and which document?). Do not read whole documents: the role of a file, not its content, is at stake. Correct what the scan got wrong, and note what you changed and why.

2. **Propose** an architecture, one role per path, the most specific path holding where two overlap:
   - `audited`: what an audit checks and may fix;
   - `original`, `prior-version`: earlier versions, read-only, never fixed (the original as first written or submitted; the later versions before the current one);
   - `normative`: documents whose definitions the audited ones use, given to the reviewers with them;
   - `sources`: references and bibliographic material, frozen, used to check citations;
   - `oracle`: a verification artifact, with its command run from the root (a mechanized development and `lake -d <dir> build`, a reference model, a test runner) and, for a mechanization, its correspondence table and where guard modules go (a place its command builds, without changing its build files);
   - `ignored`: what the audit must neither read nor touch (session history such as `.forge/`, generated or vendored material that would mislead a reader).

   A path not listed is read-only and readable: a README, a license, the project's code. With it, the **profile** of each audited path: `formal` (theory, proofs, algorithms, formal specifications) is the only profile that exists; for a document of another kind (requirements, UI specification, related work, an experimental protocol), say so plainly: it can be audited with `formal`, which suits it poorly, or left out. And the **mapped pairs**, the audited documents whose statements have a formal counterpart in an oracle (the correspondence table says which), which must change together: a fix of the statement includes its formal counterpart and the table (`profiles/formal.md` of the start skill, "Fixes").

   If `.specaudit.md` or `.specaudit/config.md` has the keys `profiles` or `normative`, the scan took them into the proposal: they belong in the architecture now, and are deprecated in the configuration. Say so, and offer to remove them from the configuration once the file is written (with the user's answer, in the same commit question as step 4).

   If `SPECAUDIT_ARCH.md` already exists, propose changes rather than a new file: run `scan.py --root "<root>" --diff`, which compares the proposal with the file, and present only the differences. A row the user wrote on purpose (a role the scan does not infer, a pattern, a description) is kept unless they ask to change it: the scan reads names and markers, not intentions.

3. **Confirm.** Show the proposal as a table, one row per path (path, role, profile, description, and for an oracle its command, correspondence table and guard location), then the mapped pairs, then the questions left open, each with your recommendation. Then ask with AskUserQuestion (header "Architecture"):
   - **Accept** (Recommended when no question is open): write it as shown;
   - **Adjust**: the user says what to change (the free answer); apply it, show the table again and ask again;
   - **Cancel**: write nothing.

   Ask the open questions in the same call when they are few (four questions at most per call; group the rest by kind). Never write without that answer. Where no question can be asked (a non-interactive session, `claude -p`, an eval), print the proposal, in the file's format (step 4), the open questions after it, and say that nothing was written and that `/spec-audit:init` must be run interactively, or the file written by hand, before any audit. Then stop.

4. **Write `SPECAUDIT_ARCH.md`** at the root, in the format below: `scan.py --root "<root>"` (without `--json`) renders the proposal in it; apply the user's adjustments to that text, or edit the existing file row by row when it already exists. Check it with:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/../start/references/arch.py" require --root "<root>"
   ```

   which must pass (exit 0) and may print warnings (a path listed but not found, a profile that does not exist yet); report them. Then offer, with AskUserQuestion (header "Commit"), to commit the file alone: **Commit it** (Recommended: the audit's worktree holds only what git tracks, so an uncommitted architecture is missing there), with `git add -- SPECAUDIT_ARCH.md` and `git commit -m "spec-audit: project architecture" -- SPECAUDIT_ARCH.md`, plus the configuration if the user agreed to remove its deprecated keys; or **Leave it uncommitted**. Never commit without that answer, never commit anything else, never push. Where no question can be asked, do not commit.

   End by saying what was written, and that `/spec-audit:start <document>` now follows it.

## Format of `SPECAUDIT_ARCH.md`

A short header saying what the file is (the scan writes it), then four tables under these headings, so that the file stays readable and editable by hand:

```markdown
## Paths

| Path | Role | Profile | Description |
|---|---|---|---|
| `artifacts/` | audited | formal | the revised version of the paper, and the detailed proofs |
| `source/manuscript.md` | original | — | the manuscript as first submitted |
| `source/references/` | sources | — | copies of hard-to-find references |
| `mechanization/` | oracle | — | Lean definitions and theorems |

## Oracles

| Path | Kind | Command | Correspondence | Guards |
|---|---|---|---|---|
| `mechanization/` | formal | `lake -d mechanization build` | `mechanization/CORRESPONDENCE.md` | `mechanization/Guards/` |

## Normative dependencies

| Document | Normative |
|---|---|

## Mapped pairs

| Document | Counterpart | Correspondence |
|---|---|---|
| `artifacts/manuscript-revised.md` | `mechanization/Selection/`, `mechanization/Selection.lean` | `mechanization/CORRESPONDENCE.md` |
```

- A path is relative to the root: `dir/` is a folder and everything in it; `*` matches within one segment and `**` across segments (`docs/spec-*.md`, for a document fixed in new revisions); when several rows match, the most specific holds (an exact file, then the longest literal part). A cell may list several paths, separated by commas; `—` means none.
- **Oracles**: kind `formal` (a mechanized development), `model` (a reference model or checker) or `runner` (a test runner); the command as it runs from the root, with no `cd`; the correspondence table between the documents' results and the oracle's names; where new guard modules go.
- **Normative dependencies**: the normative documents each audited document uses; a document without a row gets every `normative` path.
- **Mapped pairs**: an audited document, its formal counterpart, and the correspondence table between them; the counterpart and the table may change only together with the document.

`skills/start/references/arch.py` reads this format, for the audit and for the check above.
