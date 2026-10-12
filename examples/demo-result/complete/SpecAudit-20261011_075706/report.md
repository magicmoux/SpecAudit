# Precision audit — bubble-sort.md

## Result

- **Stop reason**: budget. `--max-iter 2` reached (phase 7, condition 6). Convergence is not established: iteration 2's cold detection was not clean (one proof gap confirmed, one ambiguity), and its two fixes were not followed by a further cold detection.
- **Iterations**: 2, each with 2 detection waves (wave 2 brought nothing new both times, so detection was saturated).
- **Errors**: 7 recorded (5 in iteration 1, 2 in iteration 2). Confirmed 5 (F-1-1, F-1-3, F-1-4, F-1-5, F-2-1), all fixed; refuted 1 (F-2-2); resolved by their cause 1 (F-1-2); undecided 0; blocked 0.
- **Suspects**: 0 added by the rule of 4.1 beyond the consequences already in the graph (the uses of F-1-1 were all graph members). Added / cleared / confirmed: 0 / 0 / 0 counted apart.
- **Form defects fixed**: 4 (D-0-1 cross-reference, D-1-1 typo, D-1-2 ambiguity, D-2-1 ambiguity). One further reviewer remark (R5 of wave 1, n = 0) was discarded as no defect.
- **Commits** (worktree branch `audit/bubble-sort`): r1 `4540811`, r2 `4694cea`, r3 `afc65ef`, r4 `aca958a`, r5 `0a319b5`; each marked incomplete in its message, the mark is not in the document.

## Cause graph

Iteration 1 (iteration 2 had two independent roots, no edges, no cycle):

- F-1-1 → F-1-2: the proof of Lemma 3 argues the false statement.
- F-1-1 → F-1-3: Corollary 5's proof applies Lemma 3; same counterexample family.
- F-1-3 → F-1-4: Algorithm 7's correctness argument applies Corollary 5.
- F-1-4 → F-1-5: Abstract and Conclusion repeat the claim that Algorithm 7 sorts, with passes starting later.

Root: F-1-1. Cycle: none.

## Modified statements

| Result | Before → after | Nature | Counterexample | Guards |
|---|---|---|---|---|
| Lemma 3 (F-1-1) | the i smallest elements at positions 1..i → the i largest at n−i+1..n; proof rewritten as a real induction | statement fix + proof repair | (2,3,1), i = 1: pass 1 gives (2,1,3), not 1 in front | `test_F_1_1.py`, `test_F_1_1_text.py` |
| Proof of Lemma 3 (F-2-1) | no sortedness step → last step (i = n − 1, position 1, n ≤ 1) added | proof completion | none (claim true; bounded check ok 21845) | `test_F_2_1.py`, `test_F_2_1_text.py` |
| Corollary 5 (F-1-3) | pass i starts at i → pass i ends at n − i + 1 | statement fix + proof repair | (3,2,1): Algorithm 2 gives (1,2,3), start-at-i gives (2,1,3) | `test_F_1_3.py`, `test_F_1_3_text.py` |
| Algorithm 7 (F-1-4) | pass i from i to n → from 1 to n − i + 1; title "growing start" → "shrinking end"; cites Corollary 5 instead of the nonexistent Corollary 8 | statement fix (algorithm) | (2,3,1): Algorithm 7 gives (2,1,3), Algorithm 2 gives (1,2,3); 12 of 24 permutations of 0..3 fail | `test_F_1_4.py`, `test_F_1_4_text.py` |
| Abstract and Conclusion (F-1-5) | passes "start further and further" / "start where the sorted part ends" → "end earlier and earlier" / "end where the sorted part begins" | statement fix, critical, applied under `--auto` | contradiction with Algorithm 7 step 1 (textual) | `test_F_1_5_text.py` |

Comparison counts n(n − 1)/2 and (n − 1)² were left unchanged and are checked by `test_F_1_4.py`. Proposition 4 and Example 6's first sentence were not touched (Example 6 was completed, D-1-2).

**Critical fix applied under `--auto`, to review**: F-1-5 changed what the Abstract and Conclusion claim about Algorithm 7's passes. F-1-4 also changed the algorithm the document proposes: the "faster variant" now shortens passes at the end instead of the start. The original variant did not sort; the claimed saving (about half the comparisons) holds for the corrected one.

## Errors

| ID | Severity | Type | Causes | Status | Fix | Guards | Commit |
|---|---|---|---|---|---|---|---|
| F-1-1 | critical | false statement | root | FIXED | Lemma 3 mirrored, proof rewritten | test_F_1_1(.py, _text.py) | r1 |
| F-1-2 | major | incomplete proof | F-1-1 | RESOLVED (by F-1-1) | proof judged to hold against fixed Lemma 3 | covered by test_F_1_1.py | r1 |
| F-1-3 | major | false statement | F-1-1 | FIXED | pass ends at n − i + 1 | test_F_1_3(.py, _text.py) | r2 |
| F-1-4 | critical | false statement | F-1-3 | FIXED | Algorithm 7 passes from 1 to n − i + 1 | test_F_1_4(.py, _text.py) | r3 |
| F-1-5 | major | inconsistency | F-1-4 | FIXED (critical, `--auto`) | Abstract, Conclusion reworded | test_F_1_5_text.py | r4 |
| F-2-1 | minor | incomplete proof | root | FIXED | one sentence closing Lemma 3's proof | test_F_2_1(.py, _text.py) | r5 |
| F-2-2 | minor | definition | root | REFUTED | none; clarification D-2-1 | lint rule | r5 |

## Open points

- **Convergence not established.** Iteration 2's fixes (a sentence in the proof of Lemma 3, a sentence in Definition 1) and all of iteration 1's statement changes were not followed by a fresh cold detection of the final text. The protocol asks for a second clean detection after a statement or scoping change. What would settle it: one more iteration (`--resume`, with a higher `--max-iter`), whose full reviewer reads the final document.
- **Wave-2 remark left unchanged**: the Correctness paragraph says Algorithm 7 "returns the same list as Algorithm 2"; with entries tracked as in D-2-1, "same list" is by value. Stability of Algorithm 7 follows directly from Proposition 4 (a sequence of passes), so no result depends on it. Mitigation if the author wants it: add "and, since it is a sequence of passes, is stable by Proposition 4" to the Correctness paragraph.
- No undecided errors, no corpus errors, no recurrences or oscillations, no pending critical fix, no results conditional on an unresolved error.

## Imprecisions

- **Proposition 4 / Definition 1** (F-2-2, refuted, `misleading_wording`): Definition 1 speaks of a sequence of integers, so "equal elements keep their relative order" can be read as a statement about values. Clarification applied (D-2-1): elements are the entries, tracked by position as they are swapped; "increasing" is weak.
- **Example 6** (D-1-2): it stopped after the first comparison of the pass, which a reader can take for the pass result. Completed to (1, 2, 3).

## Corpus

`spec-guards/` (replay: `pytest -q -p no:cacheprovider spec-guards`, 29 tests, all green on the fixed document):

- guards: `test_F_1_1.py`, `test_F_1_3.py`, `test_F_1_4.py`, `test_F_2_1.py` (witness, variants, near-case, bounded exhaustive checks, fixed seeds not needed: exhaustive over values 0..3 up to length 5–7);
- text guards: `test_F_1_1_text.py`, `test_F_1_3_text.py`, `test_F_1_4_text.py`, `test_F_1_5_text.py`, `test_F_2_1_text.py`;
- lint `test_lint.py`: numbering, cross-reference targets, delimiters, known misspellings, Example 6 shows the whole pass, conventions stated in Definition 1.

Replay on the original document (`SPEC_DOCS` pointing to the original text): 9 failed, 20 passed; the 9 are the five text guards and four lint rules, as required.

## Scope of verification

- **How**: 4 cold full reviews (2 per iteration), 8 adjudications, bounded exhaustive tests in exact integer arithmetic. Not peer review, not a proof; nothing here is machine-verified.
- **Confirmations by evidence level**: formal 0, model 0, ad hoc 5 (F-1-1, F-1-3, F-1-4 with executed counterexamples; F-2-1 with an executed bounded check of the intermediate claim; F-1-5 by comparison of two quoted passages, no script, flagged).
- **Effort per step**: reviewers at usual effort; adjudicators of critical errors at usual (F-1-1); reassessments of consequences at low (F-1-2/F-1-3, F-1-4, F-1-5); adjudicators of the two minor iteration-2 errors at medium. No escalation was needed: no verdict was UNDECIDED, no evidence level was weaker than the statement allows, no reassessment contradicted earlier steps. The F-1-5 verdict rests on reading, which is why it is flagged, not escalated.
- **Refusals**: 1. A `git log --format=…` command was refused by the don't-ask permission mode while the report was being prepared; retried as `git log --oneline` (allowed), no verdict depended on it.
- **Guard bug caught**: `test_F_1_4.py` first failed at n = 0 because of the guard's own tuple-versus-list encoding, not the document; corrected before the fix, in the same revision.
- **Oracles**: the project's pytest runner only; no mechanization or reference model exists. Session resources of the launcher were ignored.
- **Not checked**: the full text after iteration 2's fixes by a fresh reviewer; complexity beyond the comparison counts (swaps, best case, early exit); integer overflow or non-integer keys (Definition 1 fixes integers).

## Branch and closing

- Worktree: `<repo>-audit-bubble-sort`, branch `audit/bubble-sort`, base `c58def9`, commits as above plus this report's.
- Outcome: Partial, to continue (budget reached, no error left open, convergence not established).
- Recommended closing: **keep the worktree** (the launch asked for `keep`); merging is safe for the guards (all green) but the Abstract and Conclusion now describe a different algorithm from the original, which the author should read first.

## Summary of issues

| Priority | ID | Issue | Location | Status | Mitigation or solution | Effort (person-days) | Basis |
|---|---|---|---|---|---|---|---|
| P2 | — | Convergence not established: the final text has had no fresh cold detection after statement changes | whole document | open | one more iteration with a full reviewer (`--resume --max-iter 3`) | 0.1–0.3 | one short document, 5 revisions to re-read; confidence medium |
| P3 | — | Correctness paragraph: "same list" vs entries; stability of Algorithm 7 not stated there | §3 Correctness | open | add "stable by Proposition 4" | 0.05–0.1 | rewording, no dependents; confidence high |
| P3 | — | Review of the modified statements by the author (Lemma 3, its proof, Corollary 5, Algorithm 7, Abstract, Conclusion) | §2, §3, Abstract, §4 | to do | read the diff `c58def9..HEAD`, especially the changed variant | 0.2–0.5 | 6 modified passages, 4 chained results from the inventory; confidence medium |
| Done | F-1-1 | Lemma 3 false (smallest in front) | §2 | FIXED, guarded | mirrored statement, real induction | — | — |
| Done | F-1-2 | Proof of Lemma 3 not an induction | §2 | RESOLVED | rewritten with F-1-1 | — | — |
| Done | F-1-3 | Corollary 5 false (pass starts at i) | §2 | FIXED, guarded | pass ends at n − i + 1 | — | — |
| Done | F-1-4 | Algorithm 7 does not sort | §3 | FIXED, guarded | passes from 1 to n − i + 1 | — | — |
| Done | F-1-5 | Abstract and Conclusion describe the wrong variant | Abstract, §4 | FIXED, guarded (critical, `--auto`) | reworded | — | — |
| Done | F-2-1 | Sortedness of Algorithm 2 never written | §2 proof of Lemma 3 | FIXED, guarded | one sentence | — | — |
| Done | D-0-1, D-1-1, D-1-2, D-2-1 | cross-reference to Corollary 8, typo "comparisns", Example 6 incomplete, "increasing" and "element" undefined | §3, §2, §1 | FIXED, lint rules | see Imprecisions | — | — |

Totals: P1 0 rows; P2 0.1–0.3 person-days; P3 0.25–0.6 person-days (0 rows not estimated).
