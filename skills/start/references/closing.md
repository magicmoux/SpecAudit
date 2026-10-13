# Phase 8 — Closing, and the stop on request

Part of `/spec-audit:start`, whose folder is `skills/start/` of the plugin (`SKILL.md` gives its full path as `${CLAUDE_SKILL_DIR}`, which a file read afterwards does not substitute: below, `${CLAUDE_SKILL_DIR}` means that folder): read by the launcher once the audit session has written its report, by the orchestrator with `--in-session` once it has written the report, and by `/spec-audit:stop`. The terms (register, report, corpus, internal revision, "Questions only when idle") are those of `SKILL.md`; the formats of the index and of the guards are in `references/register.md`.


Closing is decided with the user, through a multiple-choice question, after they have been able to read the report. It is run by the launcher (your session) from the report and the register written by the audit session, or by you with `--in-session`.

### 8.1 Classify the outcome

| Outcome | Condition |
|---|---|
| **Success** | stop by convergence or exhaustion; corpus and lint green; no UNDECIDED error, no BLOCKED chain or suspect, no pending critical fix |
| **Partial, to continue** | stop on budget, or detection not saturated; corpus and lint green |
| **Partial, needs decision** | points awaiting a human decision: UNDECIDED error, BLOCKED chain, result conditional on an unresolved error (BLOCKED suspect), critical fix refused or pending; corpus and lint green |
| **Stopped at first error** | stop with `--fail-fast` on a confirmed error; the document unchanged |
| **Failure** | causal loop, recurrence, oscillation, non-convergence, corpus or lint red, or stop on an execution error |

### 8.2 Present the report

Summarize the audit in the session (outcome, stop reason, errors confirmed and fixed, modified statements, open points) and give the path of the full report, `<worktree>/spec-audit/<slug>/report.md`, to be read before choosing.

### 8.3 Ask the question

Use the multiple-choice question tool (AskUserQuestion), once no agent is running ("Questions only when idle"): a single question, with the header "Closing", that recalls the outcome and the report path. The options:

| Option | Effect |
|---|---|
| **Accept and merge** | merge of `audit/<slug>` into the original branch after the safety checks (8.5), then removal of the worktree and the branch |
| **Run another check** | new series of iterations in the same worktree (8.7), without merging anything |
| **Keep the worktree** | neither merge nor removal; results folder `SpecAudit-<YYYYmmdd_HHmmss>/` (8.4) committed in the original branch; decision postponed |
| **Abandon** | results folder (8.4) committed in the original branch, then removal of the worktree and the branch (8.6) |

The tool always adds a free answer ("Other").

Put the recommended option first, with "(Recommended)" at the end of its label. It is the safest option for the outcome:

| Outcome | Recommended | Also offered | Why |
|---|---|---|---|
| Success | Accept and merge | Run another check, Keep, Abandon | every fix is confirmed and guarded, the corpus is green |
| Partial, to continue | Run another check | Accept, Keep, Abandon | a new series can close the remaining points without touching the original branch |
| Partial, needs decision | Keep the worktree | Accept, Run another check, Abandon | a new pass will not settle what awaits a human decision, and keeping loses nothing |
| Stopped at first error | Keep the worktree | Run another check (a full audit from here, without `--fail-fast`), Abandon | nothing was fixed, so there is nothing to merge; the report is what the user acts on, and keeping loses nothing |
| Failure | Abandon | Keep; Accept only if corpus and lint are green | the automatic process can no longer make progress, and the results folder keeps everything |

Rules:

- Never offer "Accept" if the corpus or the lint is red.
- Do not offer "Run another check" after a causal loop, a recurrence, an oscillation or a non-convergence: a new pass would go round in circles. After a "Run another check" that fixed no new error, recommend "Keep" rather than "Run another check".
- Interpret a free answer; if it is ambiguous, ask again. Never merge or delete on an ambiguous answer.
- If the question cannot be asked (non-interactive session), or with `--keep`, apply "Keep the worktree": it is the only option that changes nothing and loses nothing.
- Record in the register the question, the recommended option and the answer, and its new state: `closed` after "Accept" or "Abandon", `suspended` after "Keep the worktree", still `running` after "Run another check".

### 8.4 Results folder

Every audit run to completion leaves its whole result in a folder of the project: one place where a reader who was not there finds what was audited, what was found, and everything needed to check it again, without the worktree, the session or the scratch directories, which do not outlive the audit.

**When**: at the closing of an audit that ran to its end, whatever its outcome (8.1) and whatever the answer to the closing question ("Accept", "Keep", "Abandon"), except a failure on an execution error. Not after "Run another check", whose series is not over: its own closing builds the folder. Not after a stop (8.9) or an execution error either: an interrupted audit has no result to record, only its state, which the archive of 8.4.1 keeps.

**Location**: `<project root>/SpecAudit-<YYYYmmdd_HHmmss>/`, where the time is the launch of the audit command, `/spec-audit:start`, recorded in the register at phase 0 (`Launched`), in the local time of the machine, to the second. The launch, not the closing, so that the folder names the audit the user started; a `--resume` continues the same audit and keeps its launch time.

**The name was reserved at launch** (`references/launch.md`, step 5, with `mkdir` in the original repository, `-2`, `-3`… on a collision): use it as the register records it, in the worktree where you build the folder, its README, the index entry and the register's closing entry. Never compute it again at closing: two audits launched in the same second would compute the same name, and the second closing would land on the first one's folder.

**Build it in the worktree**, from the register, after the answer to the closing question and before any merge or removal. In the default mode, the report's `## Consumption` section is already measured by then (`references/launch.md`, step 6, "Consumption"); if it still holds only its placeholder line, run that step first, so that the copy in the folder carries the measure. Copy into it, never move: `spec-audit/<slug>/` stays the audit's working state, where the launcher reads the report in the default mode, and where a `--resume`, a stop or a replay of phase 8 look for the register, the inventory and the report.

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
- **The fixed document(s)**, at the root, under a variant of the original name, `<name>.fixed<ext>` (`selection.md` → `selection.fixed.md`; keeping the path relative to the repository root if the document is in a subfolder), copied from the head of `audit/<slug>`. A variant, so that the fixed copy can never be taken for the original in `source/`, nor overwrite it when someone copies the folder's files elsewhere; the extension is kept, so the copy still opens and renders as the original does. If the version convention created a new revision under its own name, use that name instead. The copy is made only when every error could be fixed by the audit, that is, every confirmed error is FIXED or RESOLVED, none is UNDECIDED, ESCALATED or BLOCKED, no critical fix is pending or refused, and the corpus and the lint are green. Otherwise leave it out, and say in the README why and where the fixes are (`resources/corrections.patch`, the branch): a fixed copy placed beside the report reads as a sound version of the document, which it is not while an error stays open. When detection was not saturated, the README says so next to the copy: every error found is fixed, which is not the same as no error left.
- **`source/`**: the files the audit took as input, as they were at its base, not as fixed: the document(s), their normative dependencies, the project's architecture (`SPECAUDIT_ARCH.md`), the audit configuration (`.specaudit.md`, `.specaudit/`), and the unversioned inputs copied at phase 0. Take the versioned ones from the base commit (`git -C "<worktree>" show <base>:<path>`), keeping their paths relative to the repository root. The fixed versions are in the branch and in `resources/corrections.patch`; the starting point is what a later reader can no longer find once the branch has moved. Two exceptions, each recorded in the README with its path, origin and SHA-256 instead of a copy: a file that holds or may hold credentials (`.env`, keys, tokens, anything the project ignores as secret), because this folder is committed in the original branch and may be pushed; and a file over 10 MB, which git already keeps at the recorded commit and would only weigh on the repository at every audit.
- **`docs/`**: the documents the audit consulted beyond the sources: internal ones (project notes, glossaries, style guides, normative references that are not dependencies of the document), external or public ones present in the repository (standards, cited papers), and `bibliography.md`: every reference of the document, with what was checked (found and consistent, fixed, or "to be checked"), from the form-defect entries of phase 5. The audit has no network: a reference that is not in the repository is listed with its source, not fetched.
- **`resources/`**: what makes the results checkable: `corpus/`, a copy of the guard corpus and the lint as they stand at closing, with the command to replay them; `replay.py`, copied from `${CLAUDE_SKILL_DIR}/references/replay.py`, and `manifest.json`, which tells it which guard belongs to which error, the command that runs it alone (the runner as the oracle table records it), whether it is a text guard, and for each document its original (`source/…`) and its fixed version: the copy at the root, or, when an error stays open and there is none, `resources/<name>.partial<ext>`, the head of `audit/<slug>`, kept out of the root for the reason given above. Guards of a pending critical fix are left out of the manifest. `python3 resources/replay.py --on fixed` then shows the fixes hold, and `--on source` that each fixed error's text guard goes red on the original, flagging any error that has none; `corrections.patch`, `git -C "<worktree>" diff <base> audit/<slug>`, which holds every fix and guard, so nothing is lost even after abandoning; `counterexamples/<F-…>/`, the script and output with which each confirmed error was executed, copied from the adjudicator's scratch directory, since that directory is not kept; and, if the oracle table names project artifacts, their commands (not copies: they belong to the project). Leave out runner caches and bytecode (`__pycache__/`, `.pytest_cache/`).
- **`README.md`**, at the root:
  - title, outcome (8.1) and stop reason, marked "Incomplete audit" after a stop;
  - the document(s) audited, who launched the audit (name and e-mail as recorded, which is the git identity of the session, not an authentication: in an automated or cloud session it may be a bot's), the launch time with the machine's UTC offset, the closing date, the answer to the closing question, and the model of the audit session;
  - identification of the sources: with git, the repository (remote URL if one is configured, otherwise its path), the original branch, the base commit, the head of `audit/<slug>` at closing and, after "Accept", the merge commit; without git, the path and SHA-256 of each source;
  - whether the fixed document is at the root, and if not, why;
  - **Attestation**: "Not attested" at closing, and how to attest: after reading the report, the person who stands by the result signs a git tag on their own machine, `git tag -s specaudit/<folder> "$(git log -1 --format=%H -- <folder>)" -m "Attest <folder>: …"`, and `/spec-audit:attest` checks it. Say that the "Launched by" identity is not an attestation, and that the audit never signs: the key must be the person's, and a session, a cloud one especially, may sign with its own;
  - a table of contents with a relative link to every file and folder of the results folder, each with one line saying what it holds, including the files referenced but not copied;
  - how to replay: `git apply --3way resources/corrections.patch`;
  - **Tests**, when test suites exist (the audit's corpus, the project's own suites in the oracle table): for each suite, what it covers, its command and where it runs (from this folder, or in the project at the recorded commit), and its last result at closing. For the audit's corpus, the two replay modes and what each should show: `python3 resources/replay.py --on fixed`, every guard green; `--on source`, the text guard of each fixed error red, the other guards green. The reader can then check the result without reading the protocol. Omit the section when there is no suite at all, rather than leaving it empty.

Record its path in the register's closing entry, as `Results folder: SpecAudit-…/`, in those words, so that it can be found by tools as well as read.

**Index.** Update the audit's entry in `SPECAUDITS.md`, written at launch with the result `RUNNING` (format and rules in `references/register.md`): its row's result becomes `FINISHED — <outcome>`, and its section gets the paragraph a reader who was not there can act on, the details table (with its `Consumption` row: the `index` value of `consumption.py --json`, or `not measured (--in-session)`), the link to the results folder, and its `| Attested |` cell set from `—` to `no`, the word, since the folder now exists to be attested (only `/spec-audit:attest` changes it afterwards, from what it can verify). Change nothing else in the file: the other entries are the record of other audits. Write it with `index.py` (`references/register.md`, "Writing the index"): your whole entry as it must now read, which the script puts in place of the one written at launch, found by its identifier `SpecAudit-<stamp>`, under the index's lock, the other entries checked unchanged.

Commit the folder and the index on `audit/<slug>`, by path, with the register. Then bring them back:

- **In the session**: the summary from 8.2, completed with the closing performed (merge commit, worktree kept or removed) and the path of the results folder, or of the archive (8.4.1).
- **In the original branch**:
  - *Accept*: the results folder and the index arrive with the merge (8.5), with the fixed document and the corpus.
  - *Keep* or *Abandon*: first commit in the worktree any work in progress, with a message marking it as unverified. Then copy the results folder into the original repository, at its root: the folder reserved at launch is there, empty, so copy the contents into it, `cp -r "<worktree>/<folder>/." "<original repository>/<folder>/"` (the trailing `/.` matters: `cp -r <source> <existing folder>` would put the results one level down, in `<folder>/<folder>/`, where neither the index's link nor `replay.py` finds them), and check that `<original repository>/<folder>/README.md` exists. Then update its entry in the original repository's `SPECAUDITS.md` (not a copy of the worktree's index: the original holds the entries of other audits too) with `index.py --add <folder>`, which commits only these two, so as not to carry along any change from another session, and keeps the entries another audit may be writing meanwhile. If the project rules forbid this commit, pass `--no-commit` and say so.
  - *Run another check*: nothing for now; the next series ends with this same closing.

Never abandon a worktree before this return has succeeded.

#### 8.4.1 Archive of an interrupted audit

After a stop that cancels (8.9) or a failure on an execution error, there is no result to record, but nothing must be lost: copy into the original repository, under `spec-audit/<slug>/<YYYY-MM-DD>-<outcome>/`, the `report.md` (marked incomplete), the `register.md` and a `corrections.patch` produced by `git -C "<worktree>" diff <base> audit/<slug>`, which holds the fixes and the guards made so far. Commit only these files, as above. A later `--resume`, or a new audit, then produces the results folder when it runs to its end. Update the audit's entry in `SPECAUDITS.md` ("Writing the index"): `FAILED — execution error` (the section says which step failed and how) or `INTERRUPTED — cancelled`, with the archive's path instead of a results folder; and remove the empty folder reserved at launch (`rmdir`, which refuses a folder that is not empty), so that no empty name is left at the root.

### 8.5 Merge ("Accept and merge")

1. Check that the original repository is still on the branch recorded in phase 0. Otherwise, do not merge: keep the worktree and ask the question again.
2. If the original branch has moved since the base, integrate it into the worktree: `git -C "<worktree>" merge <original branch>`. A conflict on `SPECAUDITS.md` alone is expected when another audit closed meanwhile: its rows are independent, so resolve it by keeping every row of both sides, newest first, and complete the merge. On any other conflict, `git merge --abort`, keep the worktree and report that the merge is blocked; the audit itself has not failed.
3. Rerun the whole corpus and the lint in the worktree: everything must be green, otherwise keep the worktree and report.
4. Merge into the original repository: `git -C "<original repository>" merge --no-ff audit/<slug> -m "<message following the project's conventions>"`. Since the audit branch already contains the original head, no conflict is possible any more; if git refuses because of uncommitted changes in the original repository, do not force and do not stash: keep the worktree and report.
5. Remove the worktree (`git worktree remove "<worktree>"`), then the branch (`git branch -d audit/<slug>`, which refuses to delete an unmerged branch).
6. Never push.

### 8.6 Abandon ("Abandon")

After the return: `git worktree remove --force "<worktree>"`, then `git branch -D audit/<slug>`. The patch in the results folder (`resources/corrections.patch`), or in the archive after an execution error (8.4.1), makes it possible to replay all or part of the fixes, or to examine them.

### 8.7 New check ("Run another check")

Resume at phase 1 in the same worktree, with new agents and a new budget equal to `--max-passes`. The register continues (identifiers are never reassigned), the guards stay in place, and the series ends again with this phase 8.

### 8.8 Interruption

If the session is interrupted before closing (error, session closed), the worktree and the branch stay in place, and the last internal revision is the latest verified state: `--resume` resumes the audit from it (phase 0, step 5), or phase 8 can be replayed on its own.

### 8.9 Stop on request

The user can stop the audit at any time, from this session only: by pressing Esc then running `/spec-audit:stop`, or by asking in words. Esc alone interrupts your turn, not the background agents.

In the default mode, the audit runs in its own session (phase 0, step 6), launched by you. Stop it from the bottom up, so that every level reports before it ends: write the empty file `<scratch root>/stop-requested`. The session's hooks then refuse each agent's next tool call, asking it to reply at once with its state, which goes to its `partial.md`; they refuse the orchestrator's next launch, so that it waits for its agents, records the stop in the register, commits and ends; and its end writes `<worktree>-scratch/launch/ended`. Wait for that file, or for the process to end (`kill -0`, as at launch), five minutes at most: an agent sees the request only at its next tool call, and a long script may hold it. Past that delay, stop the process (its id is in the register; `taskkill /PID <pid> /T` on Windows, `kill <pid>` elsewhere), which ends its agents with it; their journals keep what they had done. Then continue at step 2, taking stock from the register and the worktree's git state (the agents it shows `running` are now `stopped`). With `--in-session`, start at step 1:

1. **Stop the agents.** Launch nothing new. Stop every audit agent still running with `TaskStop`, using the id recorded in the agent table; if that tool is not available, ask the user to stop them (`/tasks`, or the tasks pane of the desktop app). Set them to `stopped` in the agent table, and ignore any result that arrives afterwards. The agents write only to their scratch directories, so a late one cannot damage the document: stopping them saves cost and keeps the stop clean. Unlike the other questions, this stop does not wait for the agents ("Questions only when idle"): the user asked for the spending to end.
2. **Take stock.** Set the register's state to `stopping`, and record the step in progress and the uncommitted changes since the last internal revision: they are unverified.
3. **Report** in the session: the last internal revision (commit, errors fixed up to it), marked incomplete, with what it lacks (consequences not yet reassessed, errors not yet handled, detection not finished), the step in progress, the path of the register, and the interrupted agents with their scratch directories. Say that those agents will be replaced at resume by fresh agents that reuse their scratch directories, not resumed.
4. **Ask**, with AskUserQuestion: a single question with the header "Stop". It is the user, not the audit, who decides whether the last revision becomes the new base:

| Option | Effect |
|---|---|
| **Suspend** | nothing is merged or deleted; state `suspended`; `--resume` continues from the last revision |
| **Keep the last revision as the new base** | save the uncommitted changes to the document and the corpus as `spec-audit/<slug>/in-flight-<YYYY-MM-DD>.patch` and restore them to the last revision; write the report, marked "Incomplete audit — stopped at r<N>", its `## Consumption` section measured as at launch (`references/launch.md`, step 6) once the audit session has ended; commit the register, the report and the patch; then merge as in 8.5, with a merge message marking the audit incomplete. A later audit starts from this base |
| **Cancel** | write the report, marked "Incomplete audit — cancelled", its `## Consumption` section measured as above; archive it (8.4.1), then remove the worktree and the branch (8.6) |

- Put "Suspend" first, with "(Recommended)": it changes nothing and loses nothing.
- Offer "Keep the last revision" only if a revision exists, that is, once at least one error has been fixed.
- If the merge does not go through (8.5), keep the worktree: the audit stays suspended.
- Interpret a free answer; if it is ambiguous, ask again. Never merge or delete on an ambiguous answer. If the question cannot be asked, suspend.
- Record the question and the answer in the register, and set its state to `suspended` or `closed`.
- Update the audit's entry in `SPECAUDITS.md` (`references/register.md`, "Writing the index"): `INTERRUPTED — suspended`, `INTERRUPTED — kept last revision` or `INTERRUPTED — cancelled`, its section saying up to which internal revision the fixes go, what is left, and how to continue (`--resume`), or where the archive is.

## Before ending the closing

Check the register once more, since a stop, a `--resume` or the next audit reads it and nothing else: its closing entry holds the outcome, the question asked (or the rule that answered it, `--keep` or a non-interactive session), the answer, the state (`closed` or `suspended`), and the line `Results folder: SpecAudit-…/` with the name the reservation gave, or the path of the archive (8.4.1). Commit the register with the results folder.
