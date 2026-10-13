# Final report

Part of `/spec-audit:start`, whose folder is `skills/start/` of the plugin (`SKILL.md` gives its full path as `${CLAUDE_SKILL_DIR}`, which a file read afterwards does not substitute: below, `${CLAUDE_SKILL_DIR}` means that folder). Read by the orchestrator when it writes the report, at the end of phase 7. The terms (register, inventory, corpus, suspects, conditional results) are those of `SKILL.md`.

Write it in `spec-audit/<slug>/report.md`, in the worktree, and there first even when you build the results folder right after (`--in-session`): the launcher, a stop, a `--resume` and a replay of phase 8 read that file; the results folder only holds a copy. The summary to the user comes with closing (phase 8):

```markdown
# Precision audit — <document>

## Result
Stop reason, iterations, errors confirmed / refuted / resolved by their cause / undecided / blocked, suspects added / cleared / confirmed (counted apart from the errors), form defects fixed, commits.

## First error
Only with `--fail-fast`, right after "Result". The error (location, quote, type, severity), its executed counterexample and evidence level. The proposed fix of the statement: before → after, nature, and why it is the weakest change that suffices, marked "proposed, not applied". The results it may affect: its direct uses (the suspects), then every result that depends on it through them, from the inventory, each with the chain through which it uses the error; the results reached by lifting a probe's counterexample; and, first, any main result among them (abstract, conclusion, a theorem), since its fix would be critical. Then the candidates not adjudicated, by location: neither confirmed nor refuted, and not to be read as either. Say plainly that the audit stopped by choice at this error, that the rest of the document was not checked, and that a full audit is the next step.

## Cause graph
Per iteration: roots, chains, and for each edge its justification. Any cycle first.

## Modified statements
For each result touched: before → after, nature (statement fix, scoping, proof), counterexample, guards.

## Errors
| ID | Severity | Type | Causes | Status | Fix | Guards | Commit |

## Open points
Undecided errors and the chains they block, references to check, recurrences, oscillations, corpus errors (open, or settled by a guard that covers fewer cases), faulty project tests, pending critical fixes, fixes not made because they need a path the architecture does not let the audit change, architecture refusals (errors of the audit: a change it attempted outside what `SPECAUDIT_ARCH.md` allows, refused and restored), detection not saturated.
Results conditional on an unresolved error, directly or through another result: for each, the error it depends on and the chain through which it uses it.
Each open point with its mitigation: what would settle it (the adjudicator's `to_settle`), the fix or hypothesis proposed (statement before → after), and the check that would confirm it (oracle, guard to add, expert to consult).

## Imprecisions
Passages that are correct but misleading: the "ambiguity" form defects (phase 5), and the refuted errors whose adjudicator flagged a `misleading_wording`. For each: the passage, the misreading it invited, the clarification applied or proposed.

## Corpus
Guards added, lint rules added, command to replay everything.

## Scope of verification
What was checked and how (agent review, bounded exhaustive test, mechanized proof), the confirmations by evidence level (formal, model, ad hoc), the effort of each kind of step and the escalations with their triggers, the revisions the verification ran on (each agent's, from the agent table, and each verdict's, from the errors' `Verdicts`: every verdict tied to a commit of `audit/<stamp>`, on which it can be replayed; the items whose passage a fix had changed before their verification, re-quoted or resolved at the freshness check, 4.0; the agents ran one at a time), the commands refused during the audit (who, which form, and whether a retry in an allowed form settled it), since a verdict reached around a refusal deserves a second look, the account the audit was billed to, the architecture followed (`SPECAUDIT_ARCH.md`: the audited paths and their profile, the normative dependencies given, the oracles it lists, any deprecated keys of the configuration still applied), the oracles used and the session resources ignored, hypothesis discharge (edges, stated, settled by the cache, probed; verdicts RED, DISCHARGED, GREEN with their level, UNDECIDED; errors found by a probe and results reached by lifting), or that it was skipped, and what was not checked. A GREEN probe found no counterexample at its level: it is not a proof that the hypothesis holds.

## Consumption
Measured by the launcher once the session ends.

## Branch and closing
Worktree, branch `audit/<stamp>`, base, internal revisions, outcome, recommended closing option; the branch is never merged by the audit.

## Summary of issues
| Priority | ID | Issue | Location | Status | Mitigation or solution | Effort (person-days) | Basis |
Totals per priority: the sum of the estimated ranges (low sum – high sum, in person-days), with the number of rows not estimated.
```

**Summary of issues.** The last section, because it is what a reader acts on after closing the report: one row per issue of the audit, open or settled, sorted by priority, so that the work left can be planned without rereading the sections above.

- **Priority**:
  - **P1**: what leaves a claim of the document false or unsupported now: a confirmed error whose critical fix is pending or refused, a fix reverted, a causal loop, a recurrence, a result of the abstract or of the conclusion conditional on an unresolved error.
  - **P2**: undecided errors and the chains they block, unrepaired incomplete proofs, the other conditional results, open corpus errors and faulty project tests, fixes that need a path the audit may not change, architecture refusals, detection not saturated.
  - **P3**: imprecisions, references to check, form defects left open.
  - **Done**: errors and defects fixed by the audit, guarded; listed so that the summary is complete, with "—" as effort.
  - The review of the modified statements by the author is work still to do, so it is one **P3** row, the last of the P3 rows and before Done, with its effort: counted once there rather than on every Done row, and in priority order like every other row, so that the table can be read top down as the list of what is left.
- **Mitigation or solution**: the fix applied, or the one proposed in "Open points" and "Imprecisions", in one line.
- **Effort**, only when there is a basis for it: a range (`0.5–1`), never a single figure, in person-days of the author or of a domain expert. The basis column says what the range rests on: the kind of work (rewording, a hypothesis added and carried to its uses, a proof to complete, a formal counterpart to write), the number of dependent results from the inventory, and a confidence (low, medium, high). Write "not estimated" when nothing supports a figure, typically an undecided statement whose truth is unknown, which is research rather than a task. The audit sees neither the team nor its pace: an invented figure would read as more reliable than any other part of the report, so it is better absent than wrong.

**Conditional results.** Before writing "Open points", take each unresolved error: UNDECIDED or ESCALATED, CONFIRMED with a critical fix refused or pending, or with a fix reverted after a regression. From the inventory, collect every result that depends on it, directly or through another result, and list them grouped by direct use, each with what it uses. Suspects only cover the direct uses of a confirmed error; this closure also reaches the uses of an undecided error and the results that depend on a suspect. It changes nothing in the graph: the text has not changed, so there is nothing to reassess, only results that must not be presented as safe.

**Consumption.** Write the section as the template shows, the heading and that one line, nothing else: you write the report before your session ends, so you cannot know what it consumed, and the launcher replaces the line with the measure from your stream once your process has ended (`references/launch.md`, step 6, "Consumption"). Never fill it with figures of your own. With `--in-session`, write instead: "Not measured: the audit ran in the launcher's session (`--in-session`), which has no stream of its own to measure it from."

Under `## Branch and closing`, just before the summary of issues, give the worktree (path, branch `audit/<stamp>`, base, internal revisions with their commits), the audit outcome and the recommended closing option (phase 8). Say that the fixes stay on that branch, which the audit ends with a final commit and never merges: the user merges it, or not, by their own means. Never propose a merge or a pull request.

Review by agents and bounded tests are neither peer review nor proof. Never write that a proof is "verified" without saying by what; only a mechanized proof can be called machine-verified. For the same reason, never call the document or a part of it "correct": say what was checked and how ("no error found by two cold reviews; Lemma 3 guarded by a bounded check up to length 4"). The reader judges the report by what it says was done, not by its conclusion.

**Before handing over the report**, reread the summary of issues row by row, since it is the part a reader acts on and the part most easily written in a hurry at the end: the rows run P1, P2, P3 (the review of the modified statements last), then Done; and every Effort cell is a range (`0.1–0.3`), `—` on a Done row, or `not estimated`. A single figure is never right, even for a one-word fix: write the smallest honest range (`0.05–0.1`) rather than `0.1`.
