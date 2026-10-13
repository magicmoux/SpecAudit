# Phase 8 — Closing, and the stop on request

Part of `/spec-audit:start`, whose folder is `skills/start/` of the plugin (`SKILL.md` gives its full path as `${CLAUDE_SKILL_DIR}`, which a file read afterwards does not substitute: below, `${CLAUDE_SKILL_DIR}` means that folder): read by the launcher once the audit session has written its report, by the orchestrator with `--in-session` once it has written the report, and by `/spec-audit:stop`. The terms (register, report, corpus, internal revision, "Questions only when idle") are those of `SKILL.md`; the formats of the index and of the guards are in `references/register.md`.


Closing is decided with the user, through a multiple-choice question, after they have been able to read the report. It is run by the launcher (your session) from the report and the register written by the audit session, or by you with `--in-session`.

**The audit never merges.** Its fixes stay on its branch, `audit/<stamp>`, which ends with a final commit (8.4): the user merges it, or not, by their own means. Never merge it, never offer to, and never propose a pull request, in the closing question, the summary or the report. Only the results folder and the audit's index entry come back to the original branch (8.4), so that the original branch records every audit without taking any fix.

### 8.1 Classify the outcome

| Outcome | Condition |
|---|---|
| **Success** | stop by convergence or exhaustion; corpus and lint green; no UNDECIDED error, no BLOCKED chain or suspect, no pending critical fix |
| **Partial, to continue** | stop on budget, or detection not saturated; corpus and lint green |
| **Partial, needs decision** | points awaiting a human decision: UNDECIDED error, BLOCKED chain, result conditional on an unresolved error (BLOCKED suspect), critical fix refused or pending; corpus and lint green |
| **Stopped at first error** | stop with `--fail-fast` on a confirmed error; the document unchanged |
| **Failure** | causal loop, recurrence, oscillation, non-convergence, corpus or lint red, or stop on an execution error |

### 8.2 Present the report

Summarize the audit in the session (outcome, stop reason, errors confirmed and fixed, modified statements, open points) and give the path of the full report, `<worktree>/spec-audit/<slug>/report.md`, to be read before choosing, and the branch `audit/<stamp>` that holds the fixes.

### 8.3 Ask the question

Use the multiple-choice question tool (AskUserQuestion), between agents ("Questions between agents"): a single question, with the header "Closing", that recalls the outcome, the report path and the branch. The options:

| Option | Effect |
|---|---|
| **Keep the branch** | final commit on `audit/<stamp>` (8.4), results folder `SpecAudit-<stamp>/` and index entry brought back to the original branch; the branch and its worktree stay, for the user to merge, or not, by their own means (8.5) |
| **Run another check** | new series of iterations on the same branch, in the same worktree (8.7) |
| **Abandon** | final commit and return as for "Keep", then removal of the worktree and the branch (8.6); the fixes stay in the results folder's `resources/corrections.patch` |

The tool always adds a free answer ("Other"). A free answer asking to merge is answered by the branch's name and final commit, for the user to merge themselves: the audit does not merge.

Put the recommended option first, with "(Recommended)" at the end of its label. It is the safest option for the outcome:

| Outcome | Recommended | Also offered | Why |
|---|---|---|---|
| Success | Keep the branch | Run another check, Abandon | every fix is confirmed and guarded, the corpus is green: the branch is ready for the user to review and merge |
| Partial, to continue | Run another check | Keep, Abandon | a new series can close the remaining points without touching the original branch |
| Partial, needs decision | Keep the branch | Run another check, Abandon | a new pass will not settle what awaits a human decision, and keeping loses nothing |
| Stopped at first error | Keep the branch | Run another check (a full audit from here, without `--fail-fast`), Abandon | nothing was fixed; the report is what the user acts on, and keeping loses nothing |
| Failure | Abandon | Keep | the automatic process can no longer make progress, and the results folder keeps everything |

Rules:

- Do not offer "Run another check" after a causal loop, a recurrence, an oscillation or a non-convergence: a new pass would go round in circles. After a "Run another check" that fixed no new error, recommend "Keep" rather than "Run another check".
- Interpret a free answer; if it is ambiguous, ask again. Never delete on an ambiguous answer.
- If the question cannot be asked (non-interactive session), or with `--keep`, apply "Keep the branch": it is the only option that removes nothing and loses nothing.
- Record in the register the question, the recommended option and the answer, and its new state: `closed` after "Keep the branch" or "Abandon", still `running` after "Run another check".

### 8.4 Results folder

Every audit run to completion leaves its whole result in a folder of the project: one place where a reader who was not there finds what was audited, what was found, and everything needed to check it again, without the worktree, the session or the scratch directories, which do not outlive the audit.

**When**: at the closing of an audit that ran to its end, whatever its outcome (8.1) and whatever the answer to the closing question ("Keep", "Abandon"), except a failure on an execution error. Not after "Run another check", whose series is not over: its own closing builds the folder. Not after a stop (8.9) or an execution error either: an interrupted audit has no result to record, only its state, which the archive of 8.4.1 keeps.

**Location**: `<project root>/SpecAudit-<YYYYmmdd_HHmmss>/`, where the time is the launch of the audit command, `/spec-audit:start`, recorded in the register at phase 0 (`Launched`), in the local time of the machine, to the second. The launch, not the closing, so that the folder names the audit the user started; a `--resume` continues the same audit and keeps its launch time.

**The name was reserved at launch** (`references/launch.md`, step 3, with `mkdir` in the original repository, `-2`, `-3`… on a collision): use it as the register records it, in the worktree where you build the folder, its README, the index entry and the register's closing entry. Never compute it again at closing: two audits launched in the same second would compute the same name, and the second closing would land on the first one's folder.

**Final commit, first.** After the answer to the closing question, and before building the folder: record in the register its closing entry (outcome, question, answer, state, `Results folder: SpecAudit-<stamp>/`), and commit on `audit/<stamp>`, by path, everything the audit leaves on its branch: the document, the corpus (and `discharge.json`), the register, the inventory, `edges.json` and the report. In the default mode, the report's `## Consumption` section is measured by then (`references/launch.md`, step 6, "Consumption"); if it still holds only its placeholder line, run that step first. Message: `spec-audit(<slug>): final — <outcome>`, without the incomplete mark of the internal revisions. Check `git -C "<worktree>" status --porcelain` afterwards: nothing of the audit is left uncommitted. This commit is the branch's **final commit**: the folder, its README and the index entry name it by its hash, and `corrections.patch` is the diff up to it. Never merge it, nor rebase or rewrite the branch afterwards.

**Build it in the worktree**, from the register and the final commit, before any removal, outside git's view (the results folder is not committed on the audit's branch: it goes to the original branch, below). Copy into it, never move: `spec-audit/<slug>/` stays the audit's working state, where the launcher reads the report in the default mode, and where a `--resume`, a stop or a replay of phase 8 look for the register, the inventory and the report.

```text
SpecAudit-<YYYYmmdd_HHmmss>/
├── README.md         table of contents and identification
├── report.md         the final report
├── <name>.fixed<ext> the fixed document, only if every error was fixed
├── annex-*.md        the report's annexes, if any
├── register.md       the register as closed (annex)
├── inventory.md      the inventory (annex)
├── source/           the user's sources as they were at the start
├── docs/             documents consulted, and the bibliography
└── resources/        what is needed to replay the checks: corpus/, replay.py, manifest.json, corrections.patch, counterexamples/
```

- **`report.md` and its annexes**, at the root, copied from `spec-audit/<slug>/` (`cp`, not written anew: the two must be the same file; if `spec-audit/<slug>/report.md` does not exist yet, write it there first). When a section of the report grows beyond about ten entries (errors, modified statements, open points, form defects), keep in the report its summary table and move the details to `annex-<n>-<section>.md`, linked from that table: the report is what the user reads before choosing, and it must stay readable at that moment. The register and the inventory are annexes too: copy them as they stand at closing.
- **The fixed document(s)**, at the root, under a variant of the original name, `<name>.fixed<ext>` (`selection.md` → `selection.fixed.md`; keeping the path relative to the repository root if the document is in a subfolder), copied from the final commit of `audit/<stamp>`. A variant, so that the fixed copy can never be taken for the original in `source/`, nor overwrite it when someone copies the folder's files elsewhere; the extension is kept, so the copy still opens and renders as the original does. If the version convention created a new revision under its own name, use that name instead. The copy is made only when every error could be fixed by the audit, that is, every confirmed error is FIXED or RESOLVED, none is UNDECIDED, ESCALATED or BLOCKED, no critical fix is pending or refused, and the corpus and the lint are green. Otherwise leave it out, and say in the README why and where the fixes are (`resources/corrections.patch`, the branch `audit/<stamp>`): a fixed copy placed beside the report reads as a sound version of the document, which it is not while an error stays open. When detection was not saturated, the README says so next to the copy: every error found is fixed, which is not the same as no error left.
- **`source/`**: the files the audit took as input, as they were at its base, not as fixed: the document(s), their normative dependencies, the audit configuration (`.specaudit.md`, `.specaudit/`), and the unversioned inputs copied at phase 0. Take the versioned ones from the base commit (`git -C "<worktree>" show <base>:<path>`), keeping their paths relative to the repository root. The fixed versions are in the branch and in `resources/corrections.patch`; the starting point is what a later reader can no longer find once the branch has moved. Two exceptions, each recorded in the README with its path, origin and SHA-256 instead of a copy: a file that holds or may hold credentials (`.env`, keys, tokens, anything the project ignores as secret), because this folder is committed in the original branch and may be pushed; and a file over 10 MB, which git already keeps at the recorded commit and would only weigh on the repository at every audit.
- **`docs/`**: the documents the audit consulted beyond the sources: internal ones (project notes, glossaries, style guides, normative references that are not dependencies of the document), external or public ones present in the repository (standards, cited papers), and `bibliography.md`: every reference of the document, with what was checked (found and consistent, fixed, or "to be checked"), from the form-defect entries of phase 5. The audit has no network: a reference that is not in the repository is listed with its source, not fetched.
- **`resources/`**: what makes the results checkable: `corpus/`, a copy of the guard corpus and the lint as they stand at closing, with the command to replay them; `replay.py`, copied from `${CLAUDE_SKILL_DIR}/references/replay.py`, and `manifest.json`, which tells it which guard belongs to which error, the command that runs it alone (the runner as the oracle table records it), whether it is a text guard, and for each document its original (`source/…`) and its fixed version: the copy at the root, or, when an error stays open and there is none, `resources/<name>.partial<ext>`, from the final commit of `audit/<stamp>`, kept out of the root for the reason given above. Guards of a pending critical fix are left out of the manifest. `python3 resources/replay.py --on fixed` then shows the fixes hold, and `--on source` that each fixed error's text guard goes red on the original, flagging any error that has none; `corrections.patch`, `git -C "<worktree>" diff <base> <final commit>`, which holds every fix and guard, so nothing is lost even after abandoning; `counterexamples/<F-…>/`, the script and output with which each confirmed error was executed, copied from the adjudicator's scratch directory, since that directory is not kept; and, if the oracle table names project artifacts, their commands (not copies: they belong to the project). Leave out runner caches and bytecode (`__pycache__/`, `.pytest_cache/`).
- **`README.md`**, at the root:
  - title, outcome (8.1) and stop reason, marked "Incomplete audit" after a stop;
  - the document(s) audited, who launched the audit (name and e-mail as recorded, which is the git identity of the session, not an authentication: in an automated or cloud session it may be a bot's), the launch time with the machine's UTC offset, the closing date, the answer to the closing question, and the model of the audit session;
  - identification of the sources: with git, the repository (remote URL if one is configured, otherwise its path), the original branch, the base commit, the branch `audit/<stamp>` and its final commit (full hash), and whether the branch was kept or removed ("Abandon"); without git, the path and SHA-256 of each source;
  - **The fixes**: on the branch `audit/<stamp>`, which the audit did not merge: the user reviews it and merges it, or not, by their own means (`git merge audit/<stamp>`, or a pull request of their own); after "Abandon", only in `resources/corrections.patch`;
  - whether the fixed document is at the root, and if not, why;
  - **Attestation**: "Not attested" at closing, and how to attest: after reading the report, the person who stands by the result signs a git tag on their own machine, `git tag -s specaudit/<folder> "$(git log -1 --format=%H -- <folder>)" -m "Attest <folder>: …"`, and `/spec-audit:attest` checks it. Say that the "Launched by" identity is not an attestation, and that the audit never signs: the key must be the person's, and a session, a cloud one especially, may sign with its own;
  - a table of contents with a relative link to every file and folder of the results folder, each with one line saying what it holds, including the files referenced but not copied;
  - how to replay: `git apply --3way resources/corrections.patch`;
  - **Tests**, when test suites exist (the audit's corpus, the project's own suites in the oracle table): for each suite, what it covers, its command and where it runs (from this folder, or in the project at the recorded commit), and its last result at closing. For the audit's corpus, the two replay modes and what each should show: `python3 resources/replay.py --on fixed`, every guard green; `--on source`, the text guard of each fixed error red, the other guards green. The reader can then check the result without reading the protocol. Omit the section when there is no suite at all, rather than leaving it empty.

Record its path in the register's closing entry, as `Results folder: SpecAudit-…/`, in those words, so that it can be found by tools as well as read.

**Index.** Update the audit's entry in `SPECAUDITS.md`, written at launch with the result `RUNNING` (format and rules in `references/register.md`): its row's result becomes `FINISHED — <outcome>`, and its section gets the paragraph a reader who was not there can act on, the details table (with its `Branch` row: `audit/<stamp>` at its final commit, kept or removed; its `Consumption` row: the `index` value of `consumption.py --json`, or `not measured (--in-session)`), the link to the results folder, and its `| Attested |` cell set from `—` to `no`, the word, since the folder now exists to be attested (only `/spec-audit:attest` changes it afterwards, from what it can verify). Change nothing else in the file: the other entries are the record of other audits. Write it with `index.py` (`references/register.md`, "Writing the index"): your whole entry as it must now read, which the script puts in place of the one written at launch, found by its identifier `SpecAudit-<stamp>`, under the index's lock, the other entries checked unchanged.

Then bring them back, whatever the answer ("Keep" or "Abandon"):

- **In the original branch**: copy the results folder into the original repository, at its root, into the folder reserved at launch, and update its entry in the original repository's `SPECAUDITS.md` (the only index: the audit's branch never writes it) with `index.py --add <folder>`, which commits only these two, by path, so as not to carry along any change from another session, and keeps the entries another audit may be writing meanwhile. Nothing else of the audit reaches the original branch: neither the fixed document nor the corpus, which stay on `audit/<stamp>`. If the project rules forbid this commit, pass `--no-commit` and say so.
- **In the session**: the summary from 8.2, completed with the closing performed (branch `audit/<stamp>` and its final commit, kept or removed) and the path of the results folder, or of the archive (8.4.1); with the branch kept, say that merging it is the user's decision, by their own means.
- *Run another check*: nothing for now; no final commit, no results folder: the next series ends with this same closing.

Never abandon a branch before this return has succeeded.

#### 8.4.1 Archive of an interrupted audit

After a stop that cancels (8.9) or a failure on an execution error, there is no result to record, but nothing must be lost: copy into the original repository, under `spec-audit/<slug>/<YYYY-MM-DD>-<outcome>/`, the `report.md` (marked incomplete), the `register.md` and a `corrections.patch` produced by `git -C "<worktree>" diff <base> audit/<stamp>`, which holds the fixes and the guards committed so far. Commit only these files, as above. A later `--resume`, or a new audit, then produces the results folder when it runs to its end. Update the audit's entry in `SPECAUDITS.md` ("Writing the index"): `FAILED — execution error` (the section says which step failed and how) or `INTERRUPTED — cancelled`, with the archive's path instead of a results folder; and remove the empty folder reserved at launch (`rmdir`, which refuses a folder that is not empty), so that no empty name is left at the root.

### 8.5 Keep the branch ("Keep the branch")

After the return, nothing more: the branch `audit/<stamp>` and its worktree stay as the final commit left them, and the register's state is `closed`. The user reviews the branch and merges it, or not, by their own means; a later audit of the same document is a new audit, on a new branch from wherever the user's branch then is. Never merge, rebase or push the branch, and never open a pull request for it.

### 8.6 Abandon ("Abandon")

After the return: `git worktree remove --force "<worktree>"`, then `git branch -D audit/<stamp>`. The patch in the results folder (`resources/corrections.patch`), or in the archive after an execution error (8.4.1), makes it possible to replay all or part of the fixes, or to examine them.

### 8.7 New check ("Run another check")

Resume at phase 1 on the same branch, in the same worktree, with new agents and a new budget equal to `--max-passes`. The register continues (identifiers are never reassigned), the guards stay in place, and the series ends again with this phase 8, its final commit and its results folder.

### 8.8 Interruption

If the session is interrupted before closing (error, session closed), the worktree and the branch stay in place, and the last internal revision is the latest verified state: `--resume` resumes the audit from it (phase 0, step 5), or phase 8 can be replayed on its own.

### 8.9 Stop on request

The user can stop the audit at any time, from this session only: by pressing Esc then running `/spec-audit:stop`, or by asking in words. In the default mode, Esc interrupts your turn, not the audit session, which runs in its own process.

In the default mode, the audit runs in its own session (phase 0, step 6), launched by you. Stop it from the bottom up, so that every level reports before it ends: write the empty file `<scratch root>/stop-requested`. The session's hooks then refuse the running agent's next tool call, asking it to reply at once with its state, which goes to its `partial.md`; they refuse the orchestrator's next launch, so that it records the stop in the register, commits and ends; and its end writes `<worktree>-scratch/launch/ended`. Wait for that file, or for the process to end (`kill -0`, as at launch), five minutes at most: an agent sees the request only at its next tool call, and a long script may hold it. Past that delay, stop the process (its id is in the register; `taskkill /PID <pid> /T` on Windows, `kill <pid>` elsewhere), which ends its agents with it; their journals keep what they had done. Then continue at step 2, taking stock from the register and the worktree's git state (the agents it shows `running` are now `stopped`). With `--in-session`, start at step 1:

1. **Stop the agent.** Launch nothing new. The agent runs in the foreground of your turn, so the Esc that interrupted your turn interrupted it too: set it to `stopped` in the agent table, and ignore any result that arrives afterwards. Agents write only to their scratch directories, so a late one cannot damage the document.
2. **Take stock.** Set the register's state to `stopping`, and record the step in progress and the uncommitted changes since the last internal revision: they are unverified.
3. **Report** in the session: the last internal revision (commit, errors fixed up to it), marked incomplete, with what it lacks (consequences not yet reassessed, errors not yet handled, detection not finished), the step in progress, the path of the register, and the interrupted agent, if one was running, with its scratch directory. Say that it will be replaced at resume by a fresh agent that reuses its scratch directory, not resumed.
4. **Ask**, with AskUserQuestion: a single question with the header "Stop". It is the user, not the audit, who decides whether the last revision becomes the new base:

| Option | Effect |
|---|---|
| **Suspend** | nothing is deleted; state `suspended`; `--resume` continues from the last revision |
| **End at the last revision** | save the uncommitted changes to the document and the corpus as `spec-audit/<slug>/in-flight-<YYYY-MM-DD>.patch` and restore them to the last revision; write the report, marked "Incomplete audit — stopped at r<N>", its `## Consumption` section measured as at launch (`references/launch.md`, step 6) once the audit session has ended; make the final commit on `audit/<stamp>` (the register, the report and the patch), archive the report as in 8.4.1, and keep the branch, unmerged, as "Keep the branch" does (8.5). The user decides whether that revision becomes their base, by merging the branch themselves |
| **Cancel** | write the report, marked "Incomplete audit — cancelled", its `## Consumption` section measured as above; archive it (8.4.1), then remove the worktree and the branch (8.6) |

- Put "Suspend" first, with "(Recommended)": it changes nothing and loses nothing.
- Offer "End at the last revision" only if a revision exists, that is, once at least one error has been fixed.
- Interpret a free answer; if it is ambiguous, ask again. Never delete on an ambiguous answer, and never merge, whatever the answer. If the question cannot be asked, suspend.
- Record the question and the answer in the register, and set its state to `suspended` or `closed`.
- Update the audit's entry in `SPECAUDITS.md` (`references/register.md`, "Writing the index"): `INTERRUPTED — suspended`, `INTERRUPTED — ended at last revision` or `INTERRUPTED — cancelled`, its section saying up to which internal revision the fixes go, on which branch, what is left, and how to continue (`--resume`), or where the archive is.

## Before ending the closing

Check the register once more, since a stop, a `--resume` or the next audit reads it and nothing else: its closing entry holds the outcome, the question asked (or the rule that answered it, `--keep` or a non-interactive session), the answer, the state (`closed` or `suspended`), and the line `Results folder: SpecAudit-…/` with the name the reservation gave, or the path of the archive (8.4.1). It is committed in the final commit (8.4), and its copy is in the results folder. Then check that nothing was merged: the original branch has taken only the results folder and `SPECAUDITS.md` (`git -C "<original repository>" log <base>..HEAD --stat` shows no other path from the audit), and its documents are as the user left them.
