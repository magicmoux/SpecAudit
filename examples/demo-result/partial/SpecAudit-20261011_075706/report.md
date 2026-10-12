# Precision audit — bubble-sort.md

## Result

Stop reason: **budget** (`--max-iter 1` reached). One iteration, three detection waves (the third found nothing new). Not a convergence: the iteration changed statements, so a second clean detection would be required, and it was not run.

- Errors detected: 5 (F-1-1 … F-1-5). Confirmed: 5. Refuted: 0. Resolved by their cause: 0. Undecided: 0.
- Fixed: 3 (F-1-1, F-1-2, F-1-5). Confirmed with a critical fix pending: F-1-3. Blocked behind F-1-3 (critical fix, pending): F-1-4.
- Suspects: added 1 (Algorithm 7, F-1-3, through F-1-2), cleared 0, confirmed 1.
- Form defects: 3 found, 1 fixed (D-1-2), 2 open (D-1-1 waits for F-1-3, D-1-3 ambiguity).
- Commits (internal revisions, all marked incomplete): r1 `77e7262`, r2 `e705087`, r3 `1dbdbfa`.

## Cause graph

Iteration 1, no cycle. Root: F-1-1; F-1-5 is an independent root.
- F-1-1 → F-1-2: the proof of Corollary 5 applies Lemma 3, false as stated; same counterexample (2,3,1).
- F-1-2 → F-1-3: the correctness of Algorithm 7 rests on Corollary 5 (cited as "Corollary 8").
- F-1-3 → F-1-4: the abstract and the conclusion state that Algorithm 7 sorts any list.

## Modified statements

| Result | Before → after | Nature | Counterexample | Guards |
|---|---|---|---|---|
| Lemma 3 | the i smallest elements at positions 1..i → the i largest at positions n−i+1..n, in increasing order; proof rewritten as an induction | statement fix + proof repair | (2,3,1), i = 1: pass gives (2,1,3) | test_F_1_1.py, test_F_1_1_text.py |
| Corollary 5 | pass i can start at position i → pass i can stop at position n−i+1; proof rewritten | statement fix | (2,3,1): starting at i returns (2,1,3); 98 permutations of sizes 2–5 differ | test_F_1_2.py, test_F_1_2_text.py |
| Example 6 | first pass gives (1,3,2) → the pass goes on and returns (1,2,3) | statement fix | (3,1,2) | test_F_1_5.py, test_F_1_5_text.py |
| Typo (§3) | "comparisns" → "comparisons" | form | — | lint rule |

Not modified (critical, pending, see Open points): Algorithm 7, its Correctness paragraph, the abstract and the conclusion.

## Errors

| ID | Severity | Type | Causes | Status | Fix | Guards | Commit |
|---|---|---|---|---|---|---|---|
| F-1-1 | critical | false statement | root | FIXED | Lemma 3 dualised, proof rewritten | test_F_1_1(.py, _text.py) | 77e7262 |
| F-1-2 | critical | false statement | F-1-1 | FIXED | Corollary 5: pass stops at n−i+1 | test_F_1_2(.py, _text.py) | e705087 |
| F-1-3 | critical | algorithm | F-1-2 | CONFIRMED, critical fix pending | proposed: Algorithm 7 passes from 1 to n−i+1 | test_F_1_3.py (no text guard yet) | — |
| F-1-4 | critical | inconsistency (abstract, conclusion) | F-1-3 | BLOCKED by F-1-3, pending | proposed with F-1-3 | none yet | — |
| F-1-5 | minor | wrong computed example | root | FIXED | Example 6 completed | test_F_1_5(.py, _text.py) | 1dbdbfa |

## Open points

1. **Pending critical fix F-1-3 / F-1-4.** Algorithm 7 as written ("pass from position i to position n") does not sort: (3,2,1) returns (2,1,3), (2,3,1) returns (2,1,3); it sorts only for n ≤ 2. Executed (ad hoc) by an adjudicator and re-run by the orchestrator. Algorithm 7 is named by the abstract and the conclusion, so its fix changes what the document claims, and the audit session could neither ask nor use `--auto`.
   - Proposed: Algorithm 7 → "make a pass from position 1 to position n − i + 1"; Correctness → "By Corollary 5, Algorithm 7 returns the same list as Algorithm 2"; count n(n−1)/2 unchanged; title "growing start" → "shrinking end"; abstract "passes start further and further into the list" → "passes end sooner and sooner"; conclusion "starts each pass where the part of the list already sorted ends" → "ends each pass where the part of the list already sorted begins".
   - Confirming check: spec-guards/test_F_1_3.py already checks the proposed variant exhaustively (n ≤ 5 with repeated values, n = 6 permutations); a text guard is to be added once the text is approved.
2. **Results conditional on F-1-3 / F-1-4:** the abstract ("both algorithms sort any list, stably"), §3 Correctness (the sorting claim and its reference to the nonexistent "Corollary 8" (D-1-1)), §4 Conclusion ("sorts any list, stably, with about half the comparisons"). They use Corollary 5 (fixed, now saying something else than they need) and Algorithm 7. Stability of Algorithm 7 follows from Proposition 4 only if Algorithm 7 is replaced by a sorting variant.
3. **D-1-1** cross-reference "Corollary 8": left in place on purpose, it belongs to the Correctness paragraph rewritten by the pending fix; the lint rule `test_cross_references_resolve` is red until then (it was red at the baseline).
4. **Detection and convergence.** Waves 1 and 2 both missed F-1-5 (Example 6), found by the orchestrator and settled by an adjudicator; wave 3 (after the fixes) found nothing new. The iteration changed statements, so a second clean detection after the pending fix is required for convergence.

## Imprecisions

- **D-1-3** Proposition 4: "two equal elements of L keep their relative order" — on lists of integers, equal elements are indistinguishable, so stability has no content as stated. Misreading invited: that the claim is vacuous or meaningless. Clarification proposed, not applied (it could shift what the proposition claims): say that elements are tracked by their position of origin (or that the argument holds for records ordered by an integer key).

## Corpus

Directory `spec-guards/`. Guards added: test_F_1_1.py, test_F_1_1_text.py, test_F_1_2.py, test_F_1_2_text.py, test_F_1_3.py, test_F_1_5.py, test_F_1_5_text.py. Lint (`test_lint.py`): numbering, cross-references, misspellings (D-1-2), delimiters. Replay: `pytest -q -p no:cacheprovider spec-guards` — last run: 25 passed, 1 failed (`test_cross_references_resolve`, D-1-1, red since the baseline and expected until F-1-3 is fixed).

## Scope of verification

Checked: three cold full reviews (agents, no history), each reported error judged by a fresh adjudicator with an executed counterexample, exhaustive checks on small domains (n ≤ 5 with repeated values, n = 6 permutations) for Lemma 3, Corollary 5 and the proposed Algorithm 7 variant. Confirmations by evidence level: formal 0, model 0, ad hoc 5 (F-1-1, F-1-2, F-1-3, F-1-5 and the reassessments), no oracle existed. Efforts: reviewers and the adjudicator of F-1-1 at the usual effort; reassessments of F-1-2 and F-1-3 at low; F-1-5 at medium; preflight probes at low; no escalation. Refused commands: 1 (`git log --format=%h\ %s`, retried as `git log --oneline` with success; no verdict depended on it). Session resources ignored: none loaded.
Not checked: Proposition 4 beyond the reviewers' reading (no counterexample sought beyond the bounded tests); the proof text of the rewritten Lemma 3 and Corollary 5 is checked by bounded tests and by no reviewer other than wave 3, not by a mechanized proof; no bibliography exists. Review by agents and bounded tests is neither peer review nor proof.

## Branch and closing

Worktree `<repo>-audit-bubble-sort`, branch `audit/bubble-sort`, base `c58def9`, commits `77e7262`, `e705087`, `1dbdbfa` and the final report commit. Outcome: **Partial, needs decision** (a critical fix is pending). Closing: `--keep` was given, so "Keep the worktree"; nothing is merged. Recommended next step: approve or amend the F-1-3 / F-1-4 fix, then run another audit pass.

## Summary of issues

| Priority | ID | Issue | Location | Status | Mitigation or solution | Effort (person-days) | Basis |
|---|---|---|---|---|---|---|---|
| P1 | F-1-3 | Algorithm 7 does not sort ((3,2,1) → (2,1,3)) | §3 Algorithm 7, Correctness | CONFIRMED, fix pending | passes from 1 to n−i+1, correctness by Corollary 5 | 0.1–0.3 | rewording an algorithm and its correctness line; 2 dependent places; confidence high |
| P1 | F-1-4 | Abstract and conclusion claim Algorithm 7 sorts any list, stably | Abstract, §4 | BLOCKED by F-1-3 | reword to "shrinking end" | 0.05–0.2 | two sentences; confidence high |
| P2 | — | Convergence not established: second clean detection needed after the pending fix | whole document | open | rerun the audit once F-1-3 is decided | 0.2–0.5 | one more iteration; confidence medium |
| P3 | D-1-1 | Reference to nonexistent "Corollary 8" | §3 Correctness | open (with F-1-3) | becomes "Corollary 5" in the rewritten line | 0.05–0.1 | one reference; confidence high |
| P3 | D-1-3 | Stability of integers is vacuous as stated | Proposition 4 | open | track elements by position of origin | 0.1–0.3 | rewording a statement; confidence medium |
| P3 | — | Author's review of the modified statements | Lemma 3, Corollary 5, Example 6 | to do | read the three rewritten proofs | 0.2–0.5 | three short proofs; confidence medium |
| Done | F-1-1 | Lemma 3 stated the wrong end of the list | §2 | FIXED, guarded | dual statement, proof rewritten | — | — |
| Done | F-1-2 | Corollary 5 false | §2 | FIXED, guarded | pass stops at n−i+1 | — | — |
| Done | F-1-5 | Example 6 wrong pass result | §2 | FIXED, guarded | pass completed, (1,2,3) | — | — |
| Done | D-1-2 | Typo "comparisns" | §3 | FIXED, lint rule | "comparisons" | — | — |

Totals per priority: P1 0.15–0.5, P2 0.2–0.5, P3 0.35–0.9 person-days; 0 rows not estimated.
