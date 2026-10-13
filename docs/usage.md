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
- "Audit the format specification in `docs/format.md`, three passes at most."

State the document's **normative dependencies** (the files whose definitions it uses) in your request: the reviewers will receive them along with it.

## Parameters

| Parameter | Default | Effect |
|---|---|---|
| `<document>` | — | the audited file or files |
| `--corpus <dir>` | the project's existing verification corpus, otherwise `spec-guards/` | where guards are written; the conventions of the existing corpus (headers, naming, runner) are followed |
| `--max-passes N` | 5 | how many times the document is audited at most: each pass detects and fixes, and the next one audits the fixed document again; `--max-iter` is a deprecated alias |
| `--auto` | no | also applies critical fixes (statement of a main result changed, result withdrawn) without waiting for your approval; they are flagged in the report |
| `--resume` | no | resumes an interrupted or suspended audit from its register, in its existing worktree, from its last internal revision |
| `--base <ref>` | `HEAD` | starting branch or commit of the worktree |
| `--no-worktree` | no | works in the current directory, when it is already isolated for the audit |
| `--in-session` | no | runs the orchestrator in your session; by default the audit runs in a session of its own, started in the worktree with the file tools, Bash, the two agents and the project's oracles, and nothing of your session |
| `--model <family\|id>` | your session's family | model of the audit session, inherited by its agents: a family alias (`opus`, `sonnet`, `fable`, `haiku`) or a full model id; ignored with `--in-session`, where the agents inherit your session's model |
| `--model-version <v>` | `latest` | version of that family, `5.5` for instance; `latest` passes the alias, a version passes `claude-<family>-<version>` (`claude-opus-5-5`); ignored when `--model` is a full id |
| `--keep` | no | at closing, asks no question and keeps the worktree; the results folder and the index entry still come back to your branch |
| `--uniform-effort` | launch every agent at its usual effort: no lowered effort for narrow steps, no escalation |
| `--account <email>` | asked at launch | the account the audit session (`claude -p`) is billed to, as `claude auth status` names it. Without it, the launch shows the account the CLI uses and asks you to confirm it, use another, or run in your session; with it, the launch checks it and stops on a mismatch. Required in a non-interactive session |
| `--pause-at <N \| session=N,week=N \| off>` | `session=75,week=50` | pauses the audit once the account's usage reaches N % of its five-hour session window or of its week, read from the audit session's stream; `session=80,week=70` sets each, `off` none. The orchestrator stops before launching the next agent, and the launcher resumes the audit when the window resets: automatically for the session window (up to five times), by a scheduled task you confirm, or by hand, for the week. Ignored with `--in-session` |
| `--no-auto-resume` | no | on a pause, stops instead of waiting for the session window to reset, with the time and the command to resume |
| `--fail-fast` | no | one reviewer and the hypothesis probes, then the candidates confirmed one at a time from the most upstream, and a stop at the first confirmed error, without fixing it; the report gives the proposed fix of the statement and every result it may affect. For a first look at a document, or a beta test |
| `--no-discharge` | no | skips hypothesis discharge: no probe of the use edges ([design](hypothesis-discharge.md)) |

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
  max-passes: 3
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
/spec-audit:start theory/definitions.md theory/results.md --corpus tests/theory --max-passes 3

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

   It then reserves the audit's name, `SpecAudit-<stamp>` (the launch time, `YYYYmmdd_HHmmss`), and creates the worktree `<parent of the repository>/<repository>-audit-<slug>` on the branch `audit/<stamp>`, where `<slug>` is the document name in lowercase: the branch carries the same stamp as the audit's results folder and index entry, so each audit has its own branch, even two audits of the same document. It names the session `[AUDIT] <slug>` when the app allows it (Claude desktop app), or suggests that you run `/rename [AUDIT] <slug>`: this is the session from which the audit can be stopped.

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

`--in-session` runs the orchestrator in your session instead; the oracle table binds it the same way, and it never invokes a skill or a connector during the audit.

The default mode needs the `claude` CLI on your `PATH`.


**Preflight.** Before the first review, the audit session checks that its tools work: git, each oracle, a script in the agents' scratch directory, and one probe per agent type. A tool that is configured but refused would otherwise make every confirmation undecided and waste the audit. If the preflight fails, the audit stops before reviewing anything, and the skill fixes the launch and retries, three attempts at most, without ever widening what the session may run; it then tells you which tool is refused and in which form. With `--in-session`, the permissions are yours, so it asks you.
## Output files

In the worktree:

| Path | Content |
|---|---|
| the document | fixed, following the project's version convention |
| `spec-audit/<slug>/register.md` | the audit's memory: parameters, iteration log, cause graph, error and form defect entries |
| `spec-audit/<slug>/inventory.md` | every definition, lemma, proposition, theorem and algorithm, with the results it uses |
| `spec-audit/<slug>/edges.json` | every use of a result, with the hypotheses it relies on and where the user guarantees each: what hypothesis discharge probes |
| `spec-audit/<slug>/report.md` | final report |
| `<corpus>/` (`spec-guards/` by default) | guards of each error (a text guard among them), mechanical lint script, and `discharge.json`, the probes settled so far, reused by the next audit |
| `SpecAudit-<YYYYmmdd_HHmmss>/`, `SPECAUDITS.md` | the audit's index entry from its launch, and its results folder at closing (next section) |

Commits stay on the `audit/<stamp>` branch: one **internal revision** per fixed error, plus one per iteration, then a **final commit** at closing (document, corpus, register, report). Each internal revision is a verified state (every guard green), marked incomplete in its commit message, because the consequences of the error may not have been reassessed yet. The skill commits only its own files, never merges the branch and never pushes: merging it is yours to decide, by your own means.

### One agent at a time

The audit runs its agents one after the other, in the foreground, never side by side: running them in parallel would cost the same tokens, and they would race on the project's oracles (two `lake build` on one build directory), on files, and on a text being fixed under an agent reading it. Detection reads the whole document, each reviewer fresh and unaware of the others' results. Verification then takes one item at a time, causes before consequences: before verifying an item, the orchestrator rereads its passage on the current revision (re-quoting it, or dropping it if a fix already removed the defect); the adjudicator runs on that revision, whose commit is recorded with its verdict; a confirmed error is fixed, guarded and committed; and before the next item, the inventory, the uses of hypotheses (`edges.json`) and the cause graph are brought up to date, and the uses whose texts the fix changed are probed again at once. An audit that fixes is therefore long, by design. Every verdict names the commit it was reached on, in the register and in the report's "Scope of verification", so it can be replayed on exactly that text.

## Results folder

Every audit run to completion, whatever its outcome and your answer at closing, leaves its whole result in a folder at the root of the project, named by the time you launched `/spec-audit:start`, in the machine's local time: `SpecAudit-YYYYmmdd_HHmmss/`. It arrives with the merge after "Accept", and is committed on its own after "Keep" or "Abandon". A resumed audit keeps its launch time; if the name is already taken, `-2`, `-3`… is added, and an earlier folder is never overwritten.

```text
SpecAudit-20261010_210233/
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
F=SpecAudit-20261010_210233
git tag -s "specaudit/$F" "$(git log -1 --format=%H -- "$F")" -m "Attest $F: report read; accepted"
git push origin "specaudit/$F"
```

The signature ties the folder's exact content to your GPG or SSH key (or to your e-mail, with Sigstore's `gitsign`), and GitHub shows it as "Verified". Do it on your machine, not in a cloud session: such sessions may replace git's signing program with their own, and the tag would carry the environment's signature, not yours. `/spec-audit:attest <folder>` never signs. It takes the folder to check: its name, its stamp (`20261010_210233`), or the audited source (`selection.md`, for its newest folder); with no argument, the only folder not yet attested, or a question if there are several; `--all` for every folder. It does not guess from the current directory. It checks the signed tag (`yes`, `changed since attestation` when the folder was modified after signing, `signed, not verified here` when your machine does not know the key, `invalid signature`, `unsigned tag`, `no`) and, with `--update`, records that in the index's "Attested" column.

**Index.** `SPECAUDITS.md`, at the root of the project, has an entry for **every audit launched**, from its launch, newest first. A summary table gives the date, the audited object (a file or a folder), who launched it and the result, and each row links to the audit's own section: a paragraph saying what was audited, found, fixed and left open, then the details (launch time and identity with its source, base, closing, errors confirmed and fixed, fixed copy, results folder or archive, attestation). The result is a status and a detail:

| Status | Detail |
|---|---|
| `RUNNING` | from the launch until the audit ends, and during a `--resume`; still `RUNNING` for an audit that is not running means its session died without a chance to say so |
| `FINISHED` | the outcome: `Success`, `Partial, to continue`, `Partial, needs decision`, or `Failure` with its reason |
| `INTERRUPTED` | stopped on request: `suspended`, `ended at last revision` or `cancelled` |
| `FAILED` | `preflight` (a tool refused at every attempt) or `execution error` |

The entry is committed in your branch at launch, on its own, so that an audit is never left without a trace; each audit only ever changes its own entry. The index sits at the root, with the results folders: one place to look for every audit of the project, whatever was audited, which a file next to each document could not give once a folder and a document inside it are both audited, or a document is moved.

The README identifies the sources: with git, the repository (remote URL, or path), the branch, the base commit, and the audit's branch `audit/<stamp>` with its final commit, where the fixes are; the index entry names them too. Two kinds of files are referenced (path, origin, SHA-256) rather than copied into `source/`: anything that may hold credentials (`.env`, keys), because the folder is committed and may be pushed, and files over 10 MB, which git already keeps at the recorded commit. The audit has no network access, so a cited reference that is not in the repository is listed in `docs/bibliography.md`, not downloaded.

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
| Consumption | what the audit session consumed, measured by the launcher from its stream once it has ended: tokens of the orchestrator and of each agent (input, cache write, cache read, output) with each one's share, cost per model and in total as Claude Code reports it (none per agent), and the audit's share of the account's session and week windows, per run of the session; with `--in-session`, "not measured" |
| Branch and closing | worktree, branch, base, commits, outcome and recommended closing option |
| Summary of issues | last section: every issue, sorted by priority, with its mitigation or solution and its effort in person-days |

Two caveats on the consumption. Cache reads dominate the tokens of an audit but cost far less than the rest, so an agent's share of the tokens is not its share of the cost. And a window's share is the change in the account's utilization between the first and the last request of each run: any other use of the same account meanwhile is counted in it, and a run during which the window reset has no share, which the section says instead of a figure.

The summary of issues is the list to plan from:

| Priority | Covers |
|---|---|
| P1 | a claim of the document false or unsupported now: confirmed error with a critical fix pending or refused, fix reverted, causal loop, recurrence, result of the abstract or conclusion conditional on an unresolved error |
| P2 | undecided errors and the chains they block, unrepaired incomplete proofs, other conditional results, detection not saturated |
| P3 | imprecisions, references to check, form defects left open |
| Done | errors and defects fixed and guarded by the audit; their review by the author is one P3 row, just before them |

Effort is a range in person-days of the author or a domain expert (`0.5–1`), with what it rests on (kind of work, number of dependent results in the inventory) and a confidence. It reads "not estimated" when nothing supports a figure, typically for an undecided statement whose truth is unknown: that is research, not a task, and the audit knows neither your team nor its pace. Treat the ranges as an order of magnitude to plan with, not as a quote.

### Effort per step

The audit does not launch every agent at the same effort. Cold reviews and the confirmation of critical or major errors run at the usual effort, since that is where the audit's quality is decided; narrow steps run lower: the reassessment of suspects against one fixed passage and the review of one guard at `low`, a minor ad hoc confirmation at `medium`. All agents keep the same model, so that their verdicts stay comparable. A lowered step is relaunched at the usual effort, once, when its result shows it was not easy: an undecided verdict, a failed execution, evidence weaker than the statement allows, a result that contradicts the earlier steps, or the agent itself asking for it. The agent table of the register and the report's scope of verification say which step ran at which effort, and why one was escalated. `--uniform-effort` turns the routing off.

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
| Success | stop by convergence or exhaustion, corpus and lint green, nothing pending | Keep the branch |
| Partial, to continue | budget reached or detection not saturated, corpus and lint green | Run another check |
| Partial, needs decision | undecided error, blocked chain, result conditional on an unresolved error, or pending critical fix | Keep the branch |
| Failure | causal loop, recurrence, oscillation, non-convergence, corpus or lint red, execution error | Abandon |

| Option | Effect |
|---|---|
| Keep the branch | final commit on `audit/<stamp>`; results folder `SpecAudit-YYYYmmdd_HHmmss/` and index entry committed in the original branch; the branch and its worktree stay |
| Run another check | new series of iterations on the same branch, with new agents and a new budget |
| Abandon | final commit, results folder and index entry committed in the original branch as for "Keep", then removal of the worktree and the branch; the fixes stay in `resources/corrections.patch` |

**The audit never merges.** Whatever the outcome and the answer, the fixes stay on `audit/<stamp>`, and the audit neither merges the branch nor proposes a merge or a pull request. Only the results folder and the index entry come to your branch, so that it records every audit without taking any fix. Review the branch, then merge it, or not, by your own means (`git merge audit/<stamp>`, or a pull request of your own).

"Run another check" is not offered after a causal loop, a recurrence, an oscillation or a non-convergence. An ambiguous free answer leads to the question being asked again: the skill never deletes on an ambiguous answer.

## Stopping an audit

You can stop an audit at any time, from the session that launched it only (`[AUDIT] <slug>` when it could be renamed):

1. press **Esc** to interrupt the current turn (the audit session runs in its own process, and keeps running at this point);
2. run `/spec-audit:stop`, or ask in words to stop the audit.

A slash command typed while Claude is working is queued until the end of the turn, hence Esc first. From another session, `/spec-audit:stop <document>` changes nothing and names the session that runs the audit: only that one knows the step in progress and the agents running.

The skill then stops the audit session's process, which ends the agent it was running (with `--in-session`, Esc already interrupted it), reports its last internal revision (the errors fixed up to it, marked incomplete, and what it lacks), and asks:

| Option | Effect |
|---|---|
| Suspend (recommended) | nothing is deleted; `--resume` continues from the last revision |
| End at the last revision | the unverified changes after that revision are saved as a patch, the report is written and marked incomplete, and the branch ends with a final commit, kept and not merged: merging it, so that a later audit starts from it, is yours to decide |
| Cancel | report, register and patch archived in the original branch, then the worktree and the branch are removed |

"End at the last revision" is only offered once at least one error has been fixed. If the question cannot be asked, the audit is suspended.

The stop report also names the interrupted agent, if one was running, and its scratch directory. Claude Code cannot pause an agent, so nothing is paused: at resume, the interrupted agent is replaced by a fresh one with the same message and the same scratch directory, where it finds the journal, scripts and outputs of the agent it replaces and redoes only its judgment. Since agents run one at a time, there is at most one to replace, and no agent is ever running when the skill asks you a question.

## After closing

- **Replay the guards**: the command is in the "Corpus" section of the report. From a results folder, the corpus replays on either version of the document, without the project or the worktree:

  ```bash
  cd SpecAudit-<YYYYmmdd_HHmmss>
  python3 resources/replay.py --on fixed    # every guard green: the fixes hold
  python3 resources/replay.py --on source   # each fixed error's text guard red: the corpus sees the error in the text
  ```

  Every error has a text guard, which reads the document and fails on its original wording; the other guards check an encoding of the statement and pass in both modes. `--on source` lists any error without a text guard, which a revert of the text would not show. The README of the folder has a "Tests" section with these commands, the project's own suites and their results at closing.
- **Apply the patch of a results folder** (or of an archive, `spec-audit/<slug>/<YYYY-MM-DD>-<outcome>/corrections.patch`), in whole or in part:

  ```bash
  git apply --3way SpecAudit-<YYYYmmdd_HHmmss>/resources/corrections.patch
  ```

- **Merge the fixes**, if you accept them: the audit never does. Review the branch, then merge it as you would any branch (the README of the results folder names it and its final commit):

  ```bash
  git merge audit/<stamp>
  ```

- **Resume a suspended audit**: run the skill again with `--resume`.
- **Remove a kept branch** by hand, once you have merged it or decided not to:

  ```bash
  git worktree remove "<repository>-audit-<slug>"
  git branch -D audit/<stamp>
  ```

- **Push**: the skill never pushes; that is up to you.

## Tips

- **Commit before the audit**: the worktree starts from the committed version.
- **Provide an existing corpus** with `--corpus` if the project already has tests for its theory: guards will be written following its conventions and the project's runner will be used to replay them.
- **Bound the spending** with `--max-passes` and `--model`: each pass launches several agents, on the audit session's model.
- **Long documents**: the skill splits them by sections, giving each reviewer the definitions, the notation and the list of statements, and adds a cross-section consistency pass.
- **Project rules**: what `CLAUDE.md` says (attribution, document versioning, commit policy) takes precedence over the skill; write down there the constraints specific to your documents.
- **Mechanized development**: if the project has one (Lean, Coq, Isabelle, Agda), keep in the document a correspondence table from its results to the formal theorems. The audit then confirms errors on the formal statements, and refuses an ad hoc confirmation of a statement that has a formal counterpart.
- **Bibliography**: a reference is only fixed against its source (local PDF, publisher's page, DBLP); otherwise it is marked "to be checked". Put the sources in the repository so that they can be consulted.
