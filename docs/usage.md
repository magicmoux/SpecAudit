# Usage

## Launching an audit

Open Claude Code in the git repository that contains the document, then invoke the skill:

```text
/spec-audit:spec-audit <document> [options]
```

With a manual installation (without the plugin system), the command is `/spec-audit`.

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
| `--resume` | no | resumes an interrupted audit from its register, in its existing worktree |
| `--base <ref>` | `HEAD` | starting branch or commit of the worktree |
| `--no-worktree` | no | works in the current directory, when it is already isolated for the audit |
| `--keep` | no | at closing, asks no question and keeps the worktree; only the report is brought back |

## Examples

```text
# Audit one document with default settings
/spec-audit:spec-audit docs/specification.md

# Several files, existing test corpus, smaller budget
/spec-audit:spec-audit theory/definitions.md theory/results.md --corpus tests/theory --max-iter 3

# Start from another branch than the current one
/spec-audit:spec-audit spec/protocol.md --base develop

# Unattended session: critical fixes applied, worktree kept at the end
/spec-audit:spec-audit spec/format.md --auto --keep

# Resume an interrupted audit
/spec-audit:spec-audit spec/format.md --resume
```

## Workflow, from your point of view

1. **Preparation.** The skill reads the project's rules (`CLAUDE.md`, conventions), which take precedence over its own. It may ask you a question:
   - if the document, its dependencies or the corpus have uncommitted changes: they will not exist in the worktree, so should it audit the committed version or should you commit first?
   - if the project's version convention is unclear: fix in place, or create a new revision?
   - if the folder is not a git repository: should one be initialized?

   It then creates the worktree `<parent of the repository>/<repository>-audit-<slug>` on the branch `audit/<slug>`, where `<slug>` is the document name in lowercase.
2. **Iterations.** Detection, triage, cause graph, adjudication, guards, fixes and editorial track run without intervention. The register is updated after each step.
3. **Critical fixes.** If a fix changes the statement of a main result or withdraws a result, the skill first handles everything else, then presents the pending critical fixes to you together (statement before and after, counterexample, impact) and waits for your approval. With `--auto`, it applies them and flags it.
4. **Undecided errors.** When the adjudicator cannot settle an error, it is escalated to you without any change to the document, with what would make it possible to decide; its consequences remain blocked.
5. **Closing.** The skill summarizes the audit, gives the path of the full report and asks you the closing question.

## Output files

In the worktree:

| Path | Content |
|---|---|
| the document | fixed, following the project's version convention |
| `spec-audit/<slug>/register.md` | the audit's memory: parameters, iteration log, cause graph, error and form defect entries |
| `spec-audit/<slug>/inventory.md` | every definition, lemma, proposition, theorem and algorithm, with the results it uses |
| `spec-audit/<slug>/report.md` | final report |
| `<corpus>/` (`spec-guards/` by default) | guards of each error and mechanical lint script |

Commits stay on the `audit/<slug>` branch. The skill commits only its own files and never pushes.

If you choose "Keep" or "Abandon", an archive is committed in the original branch, under `spec-audit/<slug>/<YYYY-MM-DD>-<outcome>/`: `report.md`, `register.md` and `corrections.patch` (the full diff of the audit branch, fixes and guards included).

## Reading the report

| Section | Content |
|---|---|
| Result | stop reason, iterations, count of errors by status, form defects fixed, commits |
| Cause graph | roots and chains of each iteration, with the justification of each edge; any cycle first |
| Modified statements | for each result touched: before → after, nature of the fix, counterexample, guards |
| Errors | table: identifier, severity, type, causes, status, fix, guards, commit |
| Open points | undecided errors and blocked chains, references to check, recurrences, oscillations, modified guards, pending critical fixes, detection not saturated |
| Corpus | guards and lint rules added, command to replay everything |
| Scope of verification | what was checked and how, and what was not |

### Error statuses

| Status | Meaning |
|---|---|
| DETECTED | raised by a reviewer, not yet handled |
| BLOCKED (by F-…) | consequence of an error not yet fixed: neither adjudicated nor fixed |
| CONFIRMED | confirmed by the adjudicator, with executed evidence |
| REFUTED | dismissed by the adjudicator; it stays in the register to discard the same false positive later |
| UNDECIDED | the adjudicator could not settle it; no change |
| ESCALATED | raised to the user, awaiting their decision |
| FIXED | fix applied, guards green |
| RESOLVED (by F-…) | disappeared with the fix of its cause; its case joins the cause's guards |
| RECURRENCE | reappearance of an already fixed error: the audit stops |

## Closing

The audit's outcome determines the recommended option, always the safest one:

| Outcome | Condition | Recommended option |
|---|---|---|
| Success | stop by convergence or exhaustion, corpus and lint green, nothing pending | Accept and merge |
| Partial, to continue | budget reached or detection not saturated, corpus and lint green | Run another check |
| Partial, needs decision | undecided error, blocked chain or pending critical fix | Keep the worktree |
| Failure | causal loop, recurrence, oscillation, non-convergence, corpus or lint red, execution error | Abandon |

| Option | Effect |
|---|---|
| Accept and merge | safety checks, `--no-ff` merge of `audit/<slug>` into the original branch, then removal of the worktree and the branch |
| Run another check | new series of iterations in the same worktree, with new agents and a new budget; nothing is merged |
| Keep the worktree | neither merge nor removal; report, register and patch archived in the original branch |
| Abandon | report, register and patch archived in the original branch, then removal of the worktree and the branch |

"Accept" is never offered if the corpus or the lint is red, and "Run another check" is not offered after a causal loop, a recurrence, an oscillation or a non-convergence. An ambiguous free answer leads to the question being asked again: the skill never merges or deletes on an ambiguous answer.

The merge does not happen, and the worktree is kept, if the original branch has changed since the start of the audit, if integrating its new commits causes a conflict, if the corpus or the lint turn red again after that integration, or if the original repository has uncommitted changes that get in the way of the merge.

## After closing

- **Replay the guards**: the command is in the "Corpus" section of the report.
- **Apply an archived patch**, in whole or in part:

  ```bash
  git apply --3way spec-audit/<slug>/<YYYY-MM-DD>-<outcome>/corrections.patch
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
- **Bound the spending** with `--max-iter`: each iteration launches several Opus agents.
- **Long documents**: the skill splits them by sections, giving each reviewer the definitions, the notation and the list of statements, and adds a cross-section consistency pass.
- **Project rules**: what `CLAUDE.md` says (attribution, document versioning, commit policy) takes precedence over the skill; write down there the constraints specific to your documents.
- **Bibliography**: a reference is only fixed against its source (local PDF, publisher's page, DBLP); otherwise it is marked "to be checked". Put the sources in the repository so that they can be consulted.
