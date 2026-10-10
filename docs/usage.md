# Usage

## Launching an audit

Open Claude Code in the git repository that contains the document, then invoke the skill:

```text
/spec-audit:start <document> [options]
```

With a manual installation (without the plugin system), the commands are `/spec-audit-start` and `/spec-audit-stop`.

The skill also triggers without being named, as soon as you ask to proofread, check, audit, harden or make reliable a formal document:

- "Check the proofs in `theory/chapter-3.md`."
- "Hunt for errors in the lemmas of `spec/protocol.md` before submission."
- "Audit the format specification in `docs/format.md`, three iterations at most."

State the document's **normative dependencies** (the files whose definitions it uses) in your request: the reviewers will receive them along with it.

## Parameters

| Parameter | Default | Effect |
|---|---|---|
| `<document>` | — | the audited file or files |
| `--corpus <dir>` | the project's existing verification corpus, otherwise `spec-guards/` | where guards are written; the conventions of the existing corpus (headers, naming, runner) are followed |
| `--max-iter N` | 5 | maximum number of detection → fix iterations |
| `--auto` | no | also applies critical fixes (statement of a main result changed, result withdrawn) without waiting for your approval; they are flagged in the report |
| `--resume` | no | resumes an interrupted or suspended audit from its register, in its existing worktree, from its last internal revision |
| `--base <ref>` | `HEAD` | starting branch or commit of the worktree |
| `--no-worktree` | no | works in the current directory, when it is already isolated for the audit |
| `--in-session` | no | runs the orchestrator in your session; by default the audit runs in a session of its own, started in the worktree with the file tools, Bash, the two agents and the project's oracles, and nothing of your session |
| `--model <family\|id>` | your session's family | model of the audit session, inherited by its agents: a family alias (`opus`, `sonnet`, `fable`, `haiku`) or a full model id; ignored with `--in-session`, where the agents inherit your session's model |
| `--model-version <v>` | `latest` | version of that family, `5.5` for instance; `latest` passes the alias, a version passes `claude-<family>-<version>` (`claude-opus-5-5`); ignored when `--model` is a full id |
| `--keep` | no | at closing, asks no question and keeps the worktree; only the report is brought back |

## Project configuration

A project can keep its audit settings in a configuration tracked by git, so that every audit starts from the same choices:

- **`.specaudit.md`** at the root, when the configuration is all the audit needs;
- **`.specaudit/`**, with `config.md` plus the files the audit needs that the project does not have: normative references (`normative/`) and project extensions of a profile (`profiles/<profile>.md`).

Both use one format: a YAML front matter (profile per document pattern, normative dependencies, version convention, defaults of the command's options), then free notes for the orchestrator.

```markdown
---
profiles:
  "observation-derivative-calculus*.md": formal
normative:
  "observation-derivative-calculus*.md": [42_STATE_theory.md]
version-convention: new revision ("<name> - revision N.md")
defaults:
  max-iter: 3
  corpus: mechanization/Guards
---

Scope of the theory, results not to be changed, status of the proofs.
```

An option on the command wins over `defaults`. The reviewers and the adjudicators never read the configuration, which describes the audit; they receive only the normative files it declares. If the configuration is untracked or ignored by git, the skill warns and asks before creating the worktree: track it and commit it alone (recommended), use it for this audit only (copied, SHA-256 recorded), or ignore it. The worktree holds only what git tracks, so an untracked configuration would otherwise be missing from it.

## Examples

```text
# Audit one document with default settings
/spec-audit:start docs/specification.md

# Several files, existing test corpus, smaller budget
/spec-audit:start theory/definitions.md theory/results.md --corpus tests/theory --max-iter 3

# Start from another branch than the current one
/spec-audit:start spec/protocol.md --base develop

# Unattended session: critical fixes applied, worktree kept at the end
/spec-audit:start spec/format.md --auto --keep

# Resume an interrupted audit
/spec-audit:start spec/format.md --resume
```

## Workflow, from your point of view

1. **Preparation.** The skill reads the project's rules (`CLAUDE.md`, conventions), which take precedence over its own. It may ask you a question:
   - if the document, its dependencies or the corpus have uncommitted changes: they will not exist in the worktree, so should it audit the committed version or should you commit first?
   - if the project's version convention is unclear: fix in place, or create a new revision?
   - if the folder is not a git repository: should one be initialized?
   - if a session-history folder such as tokenforge's `.forge/` is tracked by git, or with `--no-worktree`: the reviewers could read your sessions' history there. Should it be untracked and added to `.gitignore` (or a worktree used), or only ignored by the agents? An untracked `.forge/` raises no question: it never reaches the worktree.
   - if an oracle of the project cannot run from the worktree alone (toolchain missing, cache too large to share, runner not installed): what should be installed or shared?

   It then creates the worktree `<parent of the repository>/<repository>-audit-<slug>` on the branch `audit/<slug>`, where `<slug>` is the document name in lowercase. It names the session `[AUDIT] <slug>` when the app allows it (Claude desktop app), or suggests that you run `/rename [AUDIT] <slug>`: this is the session from which the audit can be stopped.

   It then establishes the **environment**: what your session exposes and the audit ignores (plugins, skills, connectors, hooks), and the project's **oracles**, every artifact that can decide statements of the document (a mechanized development such as Lean, a reference model or checker, a test runner), each with the statements it covers and its command, run once in the worktree and recorded by strength in the register. Ignored files an oracle needs are shared by a link (third-party caches), copied with their SHA-256 recorded (unversioned inputs) or rebuilt (build outputs): the baseline must be green from the worktree alone.
2. **Audit session.** Unless `--in-session` is given, the audit itself runs in a session of its own, launched by yours in the worktree (see [below](#the-audit-session)). Your session waits for it, then runs the closing from its report and the register.
3. **Iterations.** Detection, triage, cause graph, adjudication, guards, fixes and editorial track run without intervention. The register is updated after each step.
4. **Critical fixes.** If a fix changes the statement of a main result or withdraws a result, the skill first handles everything else, then presents the pending critical fixes to you together (statement before and after, counterexample, impact) and waits for your approval. With `--auto`, it applies them and flags it. In the default mode, the audit session cannot ask you: they stay pending, the report lists them, and the closing recommends keeping the worktree.
5. **Undecided errors.** When the adjudicator cannot settle an error, it is escalated to you without any change to the document, with what would make it possible to decide; its consequences remain blocked. In the default mode, the escalation is in the report.
6. **Closing.** The skill summarizes the audit, gives the path of the full report and asks you the closing question.

## The audit session

By default, your session only prepares the audit (project rules, worktree, environment, register) and closes it. The audit itself runs in a session of its own: a `claude -p` process launched from the worktree, with

- no settings file, hence none of your plugins, hooks or connectors (`--setting-sources ""`, `--strict-mcp-config`), no skill (`--disallowedTools Skill`), and nothing of your conversation or memory;
- the file tools, Bash and the Agent tool only, and the two agents of the plugin, passed with `--agents`;
- the model given by `--model` and `--model-version`, otherwise the latest of your session's family, which the two agents inherit;
- a permission mode that denies anything not allowed in advance, and an allow list that is exactly `git` (push denied) and the command of each oracle recorded in the register;
- the protocol as its system prompt, and the register's path in its request.

Its process id and session id are recorded in the register. It cannot ask you anything: a critical fix stays pending unless `--auto`, an undecided error is escalated in the report, and it never runs the closing. When it ends, your session reads the report and the register, and asks you the closing question.

`--in-session` runs the orchestrator in your session instead, as before 0.7.0; the oracle table binds it the same way, and it never invokes a skill or a connector during the audit.

The default mode needs the `claude` CLI on your `PATH`.

## Output files

In the worktree:

| Path | Content |
|---|---|
| the document | fixed, following the project's version convention |
| `spec-audit/<slug>/register.md` | the audit's memory: parameters, iteration log, cause graph, error and form defect entries |
| `spec-audit/<slug>/inventory.md` | every definition, lemma, proposition, theorem and algorithm, with the results it uses |
| `spec-audit/<slug>/report.md` | final report |
| `<corpus>/` (`spec-guards/` by default) | guards of each error and mechanical lint script |

Commits stay on the `audit/<slug>` branch: one **internal revision** per fixed error, plus one per iteration. Each one is a verified state (every guard green), marked incomplete in its commit message until closing, because the consequences of the error may not have been reassessed yet. The skill commits only its own files and never pushes.

## Results folder

Every audit run to completion, whatever its outcome and your answer at closing, leaves its whole result in a folder at the root of the project, named by the time you launched `/spec-audit:start`, in the machine's local time: `SpecAudit-YYYYmmdd_HHmm/`. It arrives with the merge after "Accept", and is committed on its own after "Keep" or "Abandon". A resumed audit keeps its launch time; if the name is already taken, `-2`, `-3`… is added, and an earlier folder is never overwritten.

```text
SpecAudit-20261010_2102/
├── README.md         outcome, identification of the sources, table of contents, how to replay
├── report.md         the final report
├── selection.fixed.md  the fixed document, under a variant of its name, only if every error was fixed
├── annex-*.md        details moved out of the report when a section exceeds about ten entries
├── register.md       the register as closed
├── inventory.md      the inventory
├── source/           the audited files as they were at the start: document(s), normative dependencies, configuration, unversioned inputs
├── docs/             documents consulted (internal, external, normative) and bibliography.md, each reference with what was checked
└── resources/        corpus/ (guards and lint), replay.py and manifest.json, corrections.patch, counterexamples/<error>/ (the executed scripts and their outputs)
```

The fixed document is placed at the root, as `<name>.fixed<ext>` so that it is never confused with the original in `source/`, only when every error could be fixed by the audit (no undecided or blocked error, no critical fix pending or refused, corpus and lint green): next to the report, a fixed copy would otherwise read as a sound version while an error is still open. In that case the fixes are in `resources/corrections.patch` and in the branch, and the README says why the copy is missing.

**Attestation.** The "Launched by" identity says who ran the audit, as git knew them; it is not a signature. To attest a result, that is, to state after reading the report that you stand by it, sign a git tag on your own machine and check it with `/spec-audit:attest`:

```bash
F=SpecAudit-20261010_2102
git tag -s "specaudit/$F" "$(git log -1 --format=%H -- "$F")" -m "Attest $F: report read; accepted"
git push origin "specaudit/$F"
```

The signature ties the folder's exact content to your GPG or SSH key (or to your e-mail, with Sigstore's `gitsign`), and GitHub shows it as "Verified". Do it on your machine, not in a cloud session: such sessions may replace git's signing program with their own, and the tag would carry the environment's signature, not yours. `/spec-audit:attest` never signs; it checks every folder of the index (`yes`, `changed since attestation` when the folder was modified after signing, `signed, not verified here` when your machine does not know the key, `invalid signature`, `unsigned tag`, `no`) and, with `--update`, records that in the index's "Attested" column.

**Index.** `SPECAUDITS.md`, at the root of the project, lists every results folder, newest first, with the source it audited (a file or a folder), who launched it (always filled: the git `user.name` of the repository, else `GIT_AUTHOR_NAME`, else the system user, else `unknown`, with its source; the e-mail is in the folder's README; in a cloud or automated session, that identity may be a bot's), whether it is attested, its launch time, base commit, outcome, closing answer, errors confirmed and fixed, and whether a fixed copy is included. Each closing adds one row and never rewrites the others. When two audits close on different branches, their rows conflict at the merge: the audit resolves that conflict itself by keeping both rows, since they are independent, and stops only on any other conflict.

The README identifies the sources: with git, the repository (remote URL, or path), the branch, the base commit, the head of the audit branch and, after a merge, the merge commit. Two kinds of files are referenced (path, origin, SHA-256) rather than copied into `source/`: anything that may hold credentials (`.env`, keys), because the folder is committed and may be pushed, and files over 10 MB, which git already keeps at the recorded commit. The audit has no network access, so a cited reference that is not in the repository is listed in `docs/bibliography.md`, not downloaded.

An interrupted audit (stopped and cancelled, or failed on an execution error) has no result to record: its report, register and `corrections.patch` are archived under `spec-audit/<slug>/<YYYY-MM-DD>-<outcome>/` instead, and the results folder comes when a resumed or new audit runs to its end. The reviewers and adjudicators of later audits never read these folders: they hold the errors already found and how they were judged.

## Reading the report

| Section | Content |
|---|---|
| Result | stop reason, iterations, count of errors by status, suspects counted apart (added / cleared / confirmed), form defects fixed, commits |
| Cause graph | roots and chains of each iteration, with the justification of each edge; any cycle first |
| Modified statements | for each result touched: before → after, nature of the fix, counterexample, guards |
| Errors | table: identifier, severity, type, causes, status, fix, guards, commit |
| Open points | undecided errors and blocked chains, results conditional on an unresolved error, directly or through another result (with the error each one depends on and the chain through which it uses it), references to check, recurrences, oscillations, modified guards, pending critical fixes, detection not saturated; each with its mitigation: what would settle it, the fix or hypothesis proposed, the check that would confirm it |
| Imprecisions | correct but misleading passages: the misreading they invited and the clarification applied or proposed |
| Corpus | guards and lint rules added, command to replay everything |
| Scope of verification | what was checked and how, the confirmations by evidence level (formal, model, ad hoc), the oracles used and the session resources ignored, and what was not checked |
| Summary of issues | last section: every issue, sorted by priority, with its mitigation or solution and its effort in person-days |

The summary of issues is the list to plan from:

| Priority | Covers |
|---|---|
| P1 | a claim of the document false or unsupported now: confirmed error with a critical fix pending or refused, fix reverted, causal loop, recurrence, result of the abstract or conclusion conditional on an unresolved error |
| P2 | undecided errors and the chains they block, unrepaired incomplete proofs, other conditional results, detection not saturated |
| P3 | imprecisions, references to check, form defects left open |
| Done | errors and defects fixed and guarded by the audit; their review is counted once, on its own row |

Effort is a range in person-days of the author or a domain expert (`0.5–1`), with what it rests on (kind of work, number of dependent results in the inventory) and a confidence. It reads "not estimated" when nothing supports a figure, typically for an undecided statement whose truth is unknown: that is research, not a task, and the audit knows neither your team nor its pace. Treat the ranges as an order of magnitude to plan with, not as a quote.

### Corpus errors

A guard can be wrong too: too strict (it rejects a valid fix), badly encoded (it models a definition differently from the text), or empty (it passes whatever the text says). Since the orchestrator writes both the guards and the fixes, it never changes a guard on its own judgment. A suspect guard (red on a fix it considers valid, green on the original, flagged by the replay, or red at the baseline) opens a corpus error `G-<iteration>-<n>`, and a fresh adjudicator judges the guard against the text, without seeing the proposed fix: FAITHFUL (the fix is wrong, and the regression rule applies), FAULTY (a new guard replaces it, red first on the original like any guard, and any case it no longer covers is listed), or UNDECIDED (your decision). Your project's own tests are never changed: one found faulty is reported to you as an open point. Corpus errors appear in the report's open points and in the summary of issues.

### Error statuses

| Status | Meaning |
|---|---|
| DETECTED | raised by a reviewer, not yet handled |
| BLOCKED (by F-…) | consequence or suspect of an error not yet fixed: neither adjudicated nor fixed |
| CONFIRMED | confirmed by the adjudicator, with executed evidence |
| REFUTED | dismissed by the adjudicator; it stays in the register to discard the same false positive later |
| UNDECIDED | the adjudicator could not settle it; no change |
| ESCALATED | raised to the user, awaiting their decision |
| FIXED | fix applied, guards green |
| RESOLVED (by F-…) | disappeared with the fix of its cause, or suspect that holds against the fixed text; its case joins the cause's guards |
| RECURRENCE | reappearance of an already fixed error: the audit stops |

A **suspect** is a result that uses a confirmed error without having been reported itself. It is correct if the error is granted, so it stays BLOCKED until the error is fixed, then is reassessed against the fixed text. Its register entry has the origin `suspect (uses F-…)`; if its cause is never fixed, the report lists it as a result conditional on an unresolved error.

### Evidence levels

Each confirmed error records the oracle that confirmed it, the strongest of the register's table that covers the statement:

| Level | Oracle | Counterexample |
|---|---|---|
| formal | the project's mechanized development (Lean, Coq, Isabelle, Agda), through the document's correspondence table | executed on the formal counterpart of the statement: `#eval`, `decide`, a property-based search, or a theorem refuting it on the witness |
| model | a reference model or checker of the project | run on the model |
| ad hoc | none covers the statement | the adjudicator's own script, in exact arithmetic |

A statement that has a formal counterpart and is confirmed only at the ad hoc level stays UNDECIDED: the adjudicator's encoding, not the text, would be judged. Guards are written for the oracle that confirmed the error: a theorem or a decided check compiled by the project's build for a formal oracle, a test of the model or of the runner otherwise.

## Closing

The audit's outcome determines the recommended option, always the safest one:

| Outcome | Condition | Recommended option |
|---|---|---|
| Success | stop by convergence or exhaustion, corpus and lint green, nothing pending | Accept and merge |
| Partial, to continue | budget reached or detection not saturated, corpus and lint green | Run another check |
| Partial, needs decision | undecided error, blocked chain, result conditional on an unresolved error, or pending critical fix | Keep the worktree |
| Failure | causal loop, recurrence, oscillation, non-convergence, corpus or lint red, execution error | Abandon |

| Option | Effect |
|---|---|
| Accept and merge | safety checks, `--no-ff` merge of `audit/<slug>` into the original branch, then removal of the worktree and the branch |
| Run another check | new series of iterations in the same worktree, with new agents and a new budget; nothing is merged |
| Keep the worktree | neither merge nor removal; results folder `SpecAudit-YYYYmmdd_HHmm/` committed in the original branch |
| Abandon | results folder committed in the original branch, then removal of the worktree and the branch |

"Accept" is never offered if the corpus or the lint is red, and "Run another check" is not offered after a causal loop, a recurrence, an oscillation or a non-convergence. An ambiguous free answer leads to the question being asked again: the skill never merges or deletes on an ambiguous answer.

The merge does not happen, and the worktree is kept, if the original branch has changed since the start of the audit, if integrating its new commits causes a conflict, if the corpus or the lint turn red again after that integration, or if the original repository has uncommitted changes that get in the way of the merge.

## Stopping an audit

You can stop an audit at any time, from the session that launched it only (`[AUDIT] <slug>` when it could be renamed):

1. press **Esc** to interrupt the current turn; the background agents keep running at this point;
2. run `/spec-audit:stop`, or ask in words to stop the audit.

A slash command typed while Claude is working is queued until the end of the turn, hence Esc first. From another session, `/spec-audit:stop <document>` changes nothing and names the session that runs the audit: only that one knows the step in progress and the agents running.

The skill then stops the audit session's process, which ends its agents (with `--in-session`, every agent of the audit), reports its last internal revision (the errors fixed up to it, marked incomplete, and what it lacks), and asks:

| Option | Effect |
|---|---|
| Suspend (recommended) | nothing is merged or deleted; `--resume` continues from the last revision |
| Keep the last revision as the new base | the unverified changes after that revision are saved as a patch, the report is written and marked incomplete, then the revision is merged into the original branch with the same safety checks as "Accept and merge"; a later audit starts from it |
| Cancel | report, register and patch archived in the original branch, then the worktree and the branch are removed |

"Keep the last revision" is only offered once at least one error has been fixed. If the question cannot be asked, the audit is suspended.

The stop report also lists the interrupted agents and their scratch directories. Claude Code cannot pause an agent, so nothing is paused: at resume, each interrupted agent is replaced by a fresh one with the same message and the same scratch directory, where it finds the `progress.md`, scripts and outputs of the agent it replaces and redoes only its judgment. For the same reason, the skill asks you a question only once no agent is running, except for this stop: a question would block the orchestrator while the agents kept running and spending.

## After closing

- **Replay the guards**: the command is in the "Corpus" section of the report. From a results folder, the corpus replays on either version of the document, without the project or the worktree:

  ```bash
  cd SpecAudit-<YYYYmmdd_HHmm>
  python3 resources/replay.py --on fixed    # every guard green: the fixes hold
  python3 resources/replay.py --on source   # each fixed error's text guard red: the corpus sees the error in the text
  ```

  Every error has a text guard, which reads the document and fails on its original wording; the other guards check an encoding of the statement and pass in both modes. `--on source` lists any error without a text guard, which a revert of the text would not show. The README of the folder has a "Tests" section with these commands, the project's own suites and their results at closing.
- **Apply the patch of a results folder** (or of an archive, `spec-audit/<slug>/<YYYY-MM-DD>-<outcome>/corrections.patch`), in whole or in part:

  ```bash
  git apply --3way SpecAudit-<YYYYmmdd_HHmm>/resources/corrections.patch
  ```

- **Resume a kept worktree**: run the skill again with `--resume`, or ask to replay only the closing of the audit.
- **Remove a kept worktree** by hand:

  ```bash
  git worktree remove "<repository>-audit-<slug>"
  git branch -D audit/<slug>
  ```

- **Push**: the skill never pushes; that is up to you.

## Tips

- **Commit before the audit**: the worktree starts from the committed version.
- **Provide an existing corpus** with `--corpus` if the project already has tests for its theory: guards will be written following its conventions and the project's runner will be used to replay them.
- **Bound the spending** with `--max-iter` and `--model`: each iteration launches several agents, on the audit session's model.
- **Long documents**: the skill splits them by sections, giving each reviewer the definitions, the notation and the list of statements, and adds a cross-section consistency pass.
- **Project rules**: what `CLAUDE.md` says (attribution, document versioning, commit policy) takes precedence over the skill; write down there the constraints specific to your documents.
- **Mechanized development**: if the project has one (Lean, Coq, Isabelle, Agda), keep in the document a correspondence table from its results to the formal theorems. The audit then confirms errors on the formal statements, and refuses an ad hoc confirmation of a statement that has a formal counterpart.
- **Bibliography**: a reference is only fixed against its source (local PDF, publisher's page, DBLP); otherwise it is marked "to be checked". Put the sources in the repository so that they can be consulted.
