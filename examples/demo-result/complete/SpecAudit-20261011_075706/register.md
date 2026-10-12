# Audit register — bubble-sort.md

- Document(s): bubble-sort.md
- Normative dependencies: none
- Corpus: spec-guards/, runner: `pytest -q -p no:cacheprovider spec-guards` (empty at launch: exit 5 "no tests ran"; the lint of step 9 is the first test and makes the baseline meaningful)
- Launched by: SpecAudit demo <demo@example.invalid> (git, cloud session)
- Launched: 20261011_075706, local time, UTC+0000
- Original repository: <repo>, remote none, branch master, head c58def9c00779118359957a4bef0ac534ea4f7f4
- Worktree: <repo>-audit-bubble-sort, branch audit/bubble-sort, base c58def9
- Scratch root: <worktree>-scratch/ (audit session)
- Preflight: passed (Read, Glob, git status, pytest --version, probe.py via python3 and via with_docs.py, both agent types at low effort; no refusal), attempt 1 of 3
- Refusals: 1 (orchestrator, Bash `git log --format=…`, "denied because Claude Code is running in don't ask mode"; retried as `git log --oneline`, allowed; no verdict depended on it)
- Stop (phase 7): budget, `--max-iter 2` reached; report written in `spec-audit/bubble-sort/report.md`; phase 8 left to the launcher
- Parameters: max-iter = 2, auto = yes, keep = yes, model = sonnet, version = latest (passed: `--model sonnet`)
- Version convention: fix in place (no project convention; no CLAUDE.md)
- Configuration: none; profile formal
- Session: 01H8eFSvhvKg75HVQviNDojv (launcher), state: suspended
- Mode: audit session (pid 21896, session <session>)
- Results folder: SpecAudit-20261011_075706 (reserved in the original repository)

## Environment

Resources of the launcher's session, ignored by the audit: plugins/skills/connectors/hooks not enumerated beyond the session's own skill list; none is used.

Session history in the project: none.

Git status of the original at launch: untracked `result.json`, `stderr.log` (empty harness files, not part of the audit); the document is committed.

Oracles of the worktree, by strength (command verified in the worktree):

| Oracle | Kind | Path | Covers | Correspondence | Command |
|---|---|---|---|---|---|
| guards | runner | spec-guards/ | the corpus (no mechanization or reference model exists) | — | `pytest -q -p no:cacheprovider spec-guards` |

All statements are therefore evidence level 3 (ad hoc) unless a guard-runner model exists. Interpreter: `python3` (3.13). `python3 -m pytest` does NOT work (pytest is an executable only).

Worktree autonomy: nothing to share or copy.

## Agents

| Name | Id | Role | Error or wave | Effort | Scratch | State |
|---|---|---|---|---|---|---|
| audit-bubble-sort-reviewer-preflight | a8a5f2bc1c7b5cc52 | reviewer | preflight | low | <scratch root>/preflight/reviewer | done |
| audit-bubble-sort-adjudicator-preflight | afdeebc1579b884ee | adjudicator | preflight | low | <scratch root>/preflight/adjudicator | done |
| audit-bubble-sort-reviewer-i1-w1-a | a072ebe27d1a77f26 | reviewer | iteration 1, wave 1, full | usual | <scratch root>/iter-1/reviewer-a | done |
| audit-bubble-sort-reviewer-i1-w2-a | a0d7c15bd832a2bf5 | reviewer | iteration 1, wave 2, full | usual | <scratch root>/iter-1/reviewer-b | done |
| audit-bubble-sort-adjudicator-F-1-1 | a4d39ccf7560b9017 | adjudicator | F-1-1 | usual (critical) | <scratch root>/iter-1/adjudicator-F-1-1 | done |
| audit-bubble-sort-adjudicator-F-1-2-F-1-3 | a97f9f993bab3cd91 | adjudicator | F-1-2, F-1-3 (reassessment of the consequences of F-1-1) | low | <scratch root>/iter-1/adjudicator-F-1-2-F-1-3 | done |
| audit-bubble-sort-adjudicator-F-1-4 | aff39a3aad7761670 | adjudicator | F-1-4 (reassessment of the consequence of F-1-3) | low | <scratch root>/iter-1/adjudicator-F-1-4 | done |
| audit-bubble-sort-adjudicator-F-1-5 | a63975188e6b89e81 | adjudicator | F-1-5 (reassessment of the consequence of F-1-4) | low | <scratch root>/iter-1/adjudicator-F-1-5 | done |
| audit-bubble-sort-reviewer-i2-w1-a | a0dff2eaf4721c41f | reviewer | iteration 2, wave 1, full | usual | <scratch root>/iter-2/reviewer-a | done |
| audit-bubble-sort-reviewer-i2-w2-a | ac26b0b26aa872e98 | reviewer | iteration 2, wave 2, full | usual | <scratch root>/iter-2/reviewer-b | done |
| audit-bubble-sort-adjudicator-F-2-1 | aab1210e362f31ab7 | adjudicator | F-2-1 | medium (minor, ad hoc level) | <scratch root>/iter-2/adjudicator-F-2-1 | done |
| audit-bubble-sort-adjudicator-F-2-2 | a43e18b58a373c8c7 | adjudicator | F-2-2 | medium (minor, ad hoc level) | <scratch root>/iter-2/adjudicator-F-2-2 | done |

## Iteration log

| Iter. | Detection waves | Saturated | Errors detected | Roots | Confirmed | Refuted | Resolved by their cause | Undecided | Blocked | Suspects | Form defects | Guards added | Corpus | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2 | yes (wave 2 brought nothing new) | 5 | 1 (F-1-1) | 4 (F-1-1, F-1-3, F-1-4, F-1-5) | 0 | 1 (F-1-2) | 0 | 0 | 0 added by 4.1 (all already consequences in the graph) | 2 fixed (+ D-0-1 baseline) | 5 test files + 5 lint rules | 24 passed; replay on the original: 7 failed, 17 passed | r4 |
| 2 | 2 | yes (wave 2 brought nothing new) | 2 | 2 (F-2-1, F-2-2) | 1 (F-2-1) | 1 (F-2-2) | 0 | 0 | 0 | 0 | 1 fixed (D-2-1) | 1 test file + text guard + 1 lint rule | 29 passed; replay on the original: 9 failed, 20 passed | r5 |

## Chain digest

| ID | Statement before → after | Nature | Guards | Open suspects | Revision |
|---|---|---|---|---|---|
| F-1-1 | Lemma 3: i smallest at 1..i → i largest at n−i+1..n; proof redone | statement fix + proof repair | test_F_1_1.py, test_F_1_1_text.py | — (F-1-2 RESOLVED, F-1-3 confirmed and fixed) | r1 |
| F-1-2 | Proof of Lemma 3 (resolved by F-1-1's rewrite, judged to hold) | — | covered by test_F_1_1.py | — | r1 |
| F-1-3 | Corollary 5: pass i starts at i → ends at n−i+1; proof redone | statement fix + proof repair | test_F_1_3.py, test_F_1_3_text.py | — (F-1-4 confirmed and fixed) | r2 |
| F-1-4 | Algorithm 7: pass i from i to n → from 1 to n−i+1; cites Corollary 5 | statement fix (algorithm) | test_F_1_4.py, test_F_1_4_text.py | — (F-1-5 confirmed and fixed) | r3 |
| F-1-5 | Abstract, Conclusion: passes "start further" / "start where the sorted part ends" → "end earlier" / "end where the sorted part begins" | statement fix (critical, `--auto`) | test_F_1_5_text.py | — | r4 |
| F-2-1 | Proof of Lemma 3: no sortedness step → last step (i = n − 1, position 1, n ≤ 1) added | proof completion | test_F_2_1.py, test_F_2_1_text.py | — | r5 |

## Internal revisions

| Rev. | Commit | Error fixed | Errors fixed so far | Consequences not yet reassessed |
|---|---|---|---|---|
| r1 | see git log | F-1-1 | 1 | F-1-2, F-1-3, F-1-4, F-1-5 |
| r2 | see git log | F-1-3 | 2 | F-1-4, F-1-5 |
| r3 | see git log | F-1-4 (+ D-0-1) | 3 | F-1-5 |
| r4 | see git log | F-1-5 (+ D-1-1, D-1-2; end of iteration 1) | 4 | none |
| r5 | see git log | F-2-1 (+ D-2-1; end of iteration 2) | 5 | none |

## Cause graph — iteration 1

- F-1-1 → F-1-2: Lemma 3's proof argues the false statement; its step "smallest element moves left until position i" is the same defect.
- F-1-1 → F-1-3: Corollary 5's proof applies Lemma 3; its counterexample (2,3,1) derives from F-1-1.
- F-1-3 → F-1-4: Algorithm 7's correctness argument applies Corollary 5; same counterexample.
- F-1-4 → F-1-5: Abstract and Conclusion claim that Algorithm 7 sorts, taken from the Correctness paragraph.

Initial roots: F-1-1. Processing order: F-1-1, F-1-2, F-1-3, F-1-4, F-1-5. Cycle: none.
Triage: wave 1 (reviewer-a) and wave 2 (reviewer-b) agree; wave 2 brought nothing new, so detection is saturated. Discarded: R5 of wave 1 (n = 0, Algorithm 2 never makes a pass when n < 2, reviewer's own confidence low, no defect).

## Errors

### F-1-1 — Lemma 3 says the i smallest elements are in front
- **Fingerprint**: [false statement] Lemma 3 — a left-to-right pass carries the largest elements to the end, not the smallest to the front — L = (2,3,1)
- **Origin**: reviewer (wave 1 R1, wave 2 R1)
- **Status**: FIXED (r1)
- **Type**: false statement; **Severity**: critical (not a main result by the document's presentation, but the cause of all the others)
- **Location**: §2 Lemma 3, "the i smallest elements of L occupy positions 1 to i, in increasing order"
- **Causes**: root; **Consequences**: F-1-2, F-1-3 (suspects: Corollary 5, Algorithm 7 and its Correctness paragraph, Abstract, Conclusion — all in the graph)
- **Probable cause**: confusion between the right-moving pass and its mirror (selection of the minimum)
- **Counterexample**: L = (2,3,1), i = 1: after pass 1 the list is (2,1,3), the text predicts 1 at position 1; Algorithm 7 on (2,3,1) returns (2,1,3), and is unsorted on 12 of the 24 permutations of 0..3. Script `<scratch root>/iter-1/adjudicator-F-1-1/t.py`, rerun by the orchestrator, output `[2, 1, 3]` / `[1, 2, 3] [2, 1, 3]` / `12 [(1, 2, 0, 3), …]`.
- **Evidence**: ad hoc (level 3; no oracle covers the statement)
- **Adjudicator's verdict**: CONFIRMED (audit-bubble-sort-adjudicator-F-1-1); no upstream cause; `Proposition 4` does not depend on Lemma 3.
- **Guards**: `spec-guards/test_F_1_1.py` (witness, variants, near-case (3,1,2), bounded exhaustive check of the fixed statement for n ≤ 5 over values 0..3, consequence on the witness) and `spec-guards/test_F_1_1_text.py`. Red first: text guard fails on the original document (original wording present); the original statement is refuted on the witness. Green after the fix: 9 passed, the only failure being the lint's D-0-1.
- **Fix**: statement fix + proof repair (combined): the i smallest at positions 1..i → the i largest at positions n − i + 1..n; the proof is rewritten as a real induction. r1.

### F-1-2 — Proof of Lemma 3 is not an induction
- **Fingerprint**: [incomplete proof] Lemma 3 proof — no base case or step, key claim false — L = (2,3,1)
- **Status**: RESOLVED (by F-1-1); **Causes**: F-1-1
- **Reassessment**: adjudicator audit-bubble-sort-adjudicator-F-1-2-F-1-3 (low) judged the rewritten proof against the fixed Lemma 3: REFUTED (the proof holds); brute force over all permutations of length ≤ 5 agrees (script `<scratch root>/iter-1/adjudicator-F-1-2-F-1-3/t.py`, output `lemma3 holds True`). Covered by the bounded check in `test_F_1_1.py`.

### F-1-3 — Corollary 5 lets pass i start at position i
- **Fingerprint**: [false statement] Corollary 5 — positions 1..i−1 are not final after i−1 passes — L = (3,2,1)
- **Status**: FIXED (r2); **Causes**: F-1-1; **Consequences**: F-1-4
- **Type**: false statement; **Severity**: major (a corollary, not a main result: not in the abstract or conclusion as such)
- **Location**: §2 Corollary 5, "the i-th pass can start at position i instead of position 1, without changing the output."
- **Origin**: consequence of F-1-1, CONFIRMED on reassessment (adjudicator audit-bubble-sort-adjudicator-F-1-2-F-1-3, low; verdict reasoned and executed, no escalation needed)
- **Counterexample**: L = (3,2,1): Algorithm 2 returns (1,2,3), the same with pass i starting at i returns (2,1,3). Script `<scratch root>/iter-1/adjudicator-F-1-2-F-1-3/t.py`, rerun by the orchestrator, output `[1, 2, 3] [2, 1, 3]`.
- **Evidence**: ad hoc
- **Probable cause**: the lemma was misapplied (Lemma 3 as originally stated put the sorted part in front)
- **Guards**: `spec-guards/test_F_1_3.py` (witness, variants, near-case (3,1,2), bounded exhaustive check on lists of length ≤ 6 over values 0..3) and `spec-guards/test_F_1_3_text.py`. Red first: text guard failed on the document before the fix; original refuted on (3,2,1). Green after.
- **Fix**: statement fix + proof repair: "start at position i" → "end at position n − i + 1", proof rewritten from Lemma 3. r2. Class guard: the same pattern (a pass bound) occurs in Algorithm 7, F-1-4.

### F-1-4 — Algorithm 7 does not sort
- **Fingerprint**: [false statement] Algorithm 7 and its Correctness paragraph — starting pass i at i skips needed comparisons — L = (2,3,1)
- **Status**: FIXED (r3); **Causes**: F-1-3; **Consequences**: F-1-5
- **Origin**: consequence of F-1-3, CONFIRMED on reassessment (adjudicator audit-bubble-sort-adjudicator-F-1-4, low; verdict executed, no escalation)
- **Type**: false statement; **Severity**: critical (Algorithm 7 is the document's headline result)
- **Location**: §3 Algorithm 7 step 1 and Correctness, "make a pass from position i to position n"; "By Corollary 8, Algorithm 7 returns the same list as Algorithm 2"
- **Counterexample**: L = (2,3,1): Algorithm 7 returns (2,1,3), Algorithm 2 returns (1,2,3). Script `<scratch root>/iter-1/adjudicator-F-1-4/t.py`, rerun by the orchestrator, output `([1, 2, 3], 4) ([2, 1, 3], 3)`, `16 10`.
- **Evidence**: ad hoc
- **Guards**: `spec-guards/test_F_1_4.py` (witness, variants, near-case (3,1,2), bounded exhaustive check of the fixed algorithm: equal to Algorithm 2 and sorted, with n(n−1)/2 and (n−1)² comparisons, n ≤ 6 over values 0..3; stability of the fixed algorithm on tagged lists) and `test_F_1_4_text.py`. Red first: text guard failed on the original wording; original refuted on the witness. One guard bug caught and corrected before the fix (tuple versus list at n = 0, the guard's own encoding, not a document defect). Green after: 21 passed.
- **Fix**: statement fix (algorithm): "pass from position i to position n" → "pass from position 1 to position n − i + 1", title "growing start" → "shrinking end", the Correctness paragraph now cites Corollary 5 (this also fixes D-0-1). Comparison counts unchanged and checked by the guard. r3.

### F-1-5 — Abstract and Conclusion claim Algorithm 7 sorts
- **Fingerprint**: [inconsistency] Abstract and §4 — claim that Algorithm 7 sorts any list, with passes starting further in — L = (2,3,1)
- **Status**: FIXED (r4); **Causes**: F-1-4; critical fix (abstract, conclusion), applied under `--auto`
- **Origin**: consequence of F-1-4, CONFIRMED on reassessment (adjudicator audit-bubble-sort-adjudicator-F-1-5, low). Type inconsistency, severity major.
- **Location**: Abstract "a variant whose passes start further and further into the list"; §4 "which starts each pass where the part of the list already sorted ends"
- **Defect**: after F-1-3/F-1-4, every pass of Algorithm 7 starts at position 1 and only its end moves; both passages describe a moving start.
- **Evidence**: the contradiction is between two quoted passages (Algorithm 7 step 1 against Abstract and Conclusion), checked by the orchestrator; no script was run, since the defect is textual and not a counterexample to a statement. Flagged: the adjudicator's own verdict was by reading.
- **Guards**: `spec-guards/test_F_1_5_text.py`. Red first: failed on the document before the fix (and on the original in the replay). Green after.
- **Fix**: statement fix (critical fix applied under `--auto`, flagged for the report): "start further and further into the list" → "end earlier and earlier in the list"; "starts each pass where the part of the list already sorted ends" → "ends each pass where the part of the list already sorted begins". The claims of sorting, stability and about half the comparisons are unchanged (checked in `test_F_1_4.py`). r4.

### F-2-1 — No statement says that Algorithm 2 sorts
- **Fingerprint**: [incomplete proof] Correctness of Algorithm 7 and Abstract — the sortedness of Algorithm 2 (Lemma 3 at i = n − 1, then position 1) is never written — no counterexample (the claim is true)
- **Origin**: reviewer (iteration 2, wave 1 R1; wave 2 as a form defect "omission")
- **Status**: FIXED (r5); **Type**: incomplete proof; **Severity**: minor; **Causes**: root; **Consequences**: none (the claim is true)
- **Adjudicator's verdict**: CONFIRMED (audit-bubble-sort-adjudicator-F-2-1, medium): the step "position 1 holds the remaining element" and the case n ≤ 1 are never written; the claim holds. Bounded check of the missing intermediate claim, script `<scratch root>/iter-2/adjudicator-F-2-1/t.py`, rerun by the orchestrator, output `ok 21845`.
- **Evidence**: ad hoc (bounded check of the intermediate claim; no counterexample exists)
- **Guards**: `spec-guards/test_F_2_1.py` (witnesses, near-case (3,1,2), bounded exhaustive check n ≤ 7 over values 0..3) and `test_F_2_1_text.py`. Red first: text guard failed before the fix and on the original. Green after: 29 passed.
- **Fix**: proof completion, one sentence at the end of the proof of Lemma 3 ("For i = n − 1 (n ≥ 2), position 1 then holds the remaining element … so Algorithm 2 sorts L; if n ≤ 1 …"). No new numbered result, as the protocol forbids introducing a result to plug a gap. r5.

### F-2-2 — Stability of a list of plain integers
- **Fingerprint**: [definition] Proposition 4 and Abstract — equal integers are indistinguishable, so "keep their relative order" needs tracked elements — none
- **Origin**: reviewer (iteration 2, wave 1 R2, low confidence)
- **Status**: REFUTED; **Type**: definition; **Severity**: minor; **Causes**: root
- **Adjudicator's verdict**: REFUTED (audit-bubble-sort-adjudicator-F-2-2, medium): the proof of Proposition 4 reasons on tracked entries, which is the standard meaning of stability for swap-based sorts; no result is false or unproven. Flagged `misleading_wording`: Definition 1 speaks of a sequence of integers, so "element" can be read as a value. Opened as ambiguity D-2-1. No script (a question of wording).
- Wave 2 also raised as form defects: ties in "the i largest elements" (Lemma 3), "increasing" versus "non-decreasing", "same list" versus same permutation of identities (Correctness). The first two are covered by D-2-1; the third is left as is (Proposition 4 already gives the stability of any sequence of passes, hence of Algorithm 7, and the change would touch guarded wording).

## Form defects

- D-0-1 — cross-reference — §3 Correctness, "By Corollary 8" → "By Corollary 5" — fixed in r3 with F-1-4 (same sentence) — baseline lint `test_cross_references_have_targets` was red on it (expected: a lint going red on an existing form defect, not a guard fault), green now; also covered by `test_F_1_4_text.py`.

- D-1-1 — typo — §3 Correctness — "comparisns" → "comparisons" — no source needed — lint rule `test_known_misspellings_absent` (list of known misspellings) — r4.
- D-1-2 — ambiguity — Example 6 — the example stopped after the first comparison of the pass ("which gives (1, 3, 2)"), which a reader can take for the result of the pass — completed with the second comparison, "then compares 3 and 2 and swaps them, which gives (1, 2, 3)" — lint rule `test_example_6_shows_the_whole_pass` — r4.
- D-2-1 — ambiguity — Definition 1 — "increasing" and "element" were not fixed — added "Below, "increasing" is meant in the weak sense (equal elements allowed), and the elements of a list are its entries, followed by position as they are swapped, so that two equal entries remain two distinct elements." — lint rule `test_conventions_stated_in_definition_1` — r5.
- Discarded: wave-1 R5 (n = 0), see triage.

## Baseline (phase 0, steps 7–9)

Inventory written (`inventory.md`). Lint `spec-guards/test_lint.py` (numbering, cross-references, delimiters) added; baseline: 2 passed, 1 failed (D-0-1 only).

## Closing

- Outcome: Partial, to continue (budget reached, no error left open, convergence not established).
- Question: not asked, `--keep` given; recommended and applied: Keep the worktree.
- Answer: Keep the worktree. State: suspended.
- Results folder: SpecAudit-20261011_075706/
