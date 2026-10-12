# Audit register — bubble-sort.md

- Document(s): bubble-sort.md
- Normative dependencies: none
- Corpus: spec-guards/, runner: `pytest -q -p no:cacheprovider spec-guards`
- Launched by: SpecAudit demo <demo@example.invalid> (git, cloud session)
- Launched: 20261011_075706, local time, UTC+0000
- Original repository: <repo>, remote none, branch master, head c58def9 (SPECAUDITS.md entry committed after)
- Worktree: <repo>-audit-bubble-sort, branch audit/bubble-sort, base c58def9
- Scratch root: <repo>-audit-bubble-sort-scratch/ (audit session); every agent's scratch directory is under it
- Preflight: passed (Read/Glob, git status, pytest --version, python3 probe, with_docs.py, both agent types at low effort; corpus-script form not probed: no lint yet), attempt 1 of 3
- Refusals: 1 (orchestrator, Bash `git log --format=%h\ %s`, denied in don't-ask mode; retried as `git log --oneline`, ok)
- Parameters: max-iter = 1, auto = no, keep = yes, model = sonnet, version = latest (passed: `--model sonnet`)
- Version convention: fix in place (no CLAUDE.md or convention; document is a single committed file)
- Configuration: none; profile formal
- Results folder: SpecAudit-20261011_075706 (reserved, empty, in original repository)
- Session: unknown, state: suspended (stopped at phase 7 (budget, max-iter 1); report written, closing done: Keep the worktree)
- Mode: audit session (pid TBD, session TBD)

## Environment

Resources of the launcher's session, ignored by the audit: not enumerated (audit session loads no settings, plugins, connectors or hooks).

Session history in the project: none. Untracked empty files result.json, stderr.log in original directory are not in the worktree.

Oracles of the worktree, by strength (every command verified in the worktree at phase 0):

| Oracle | Kind | Path | Covers | Correspondence | Command |
|---|---|---|---|---|---|
| guards | runner | spec-guards/ | the corpus (initially empty; lint added at step 9) | — | `pytest -q -p no:cacheprovider spec-guards` |

No formal or model oracle exists. Evidence will be ad hoc (python3 scripts in exact arithmetic).

Worktree autonomy: nothing to share or copy.

## Agents

| Name | Id | Role | Error or wave | Effort | Scratch | State |
|---|---|---|---|---|---|---|
| audit-bubble-sort-reviewer-preflight | adbb45576854a182f | reviewer | preflight | low | scratch/preflight/reviewer | done |
| audit-bubble-sort-adjudicator-preflight | a1a580818850bd53d | adjudicator | preflight | low | scratch/preflight/adjudicator | done |
| audit-bubble-sort-reviewer-i1-w1-a | ac5fcf9853a8959b3 | reviewer | iteration 1, wave 1, full | usual | scratch/iter-1/reviewer-a | done |
| audit-bubble-sort-reviewer-i1-w2-a | aa4f5d393edce05d9 | reviewer | iteration 1, wave 2, full | usual | scratch/iter-1/reviewer-b | done |
| audit-bubble-sort-adjudicator-F-1-1 | a56bb9a342595f66a | adjudicator | F-1-1 | usual (critical) | scratch/iter-1/adjudicator-F-1-1 | done |
| audit-bubble-sort-adjudicator-F-1-2 | a730b2dc6fbdff649 | adjudicator | F-1-2 (4.5 reassessment) | low | scratch/iter-1/adjudicator-F-1-2 | done |
| audit-bubble-sort-adjudicator-F-1-3 | a6beb157ff65559e0 | adjudicator | F-1-3 (4.5 reassessment) | low | scratch/iter-1/adjudicator-F-1-3 | done |
| audit-bubble-sort-adjudicator-F-1-5 | a5dad022b3e941f3b | adjudicator | F-1-5 | medium | scratch/iter-1/adjudicator-F-1-5 | done |
| audit-bubble-sort-reviewer-i1-w3-a | a0a82d24f6483748c | reviewer | iteration 1, wave 3, full (after fixes r1–r3) | usual | scratch/iter-1/reviewer-c | done |

(scratch = the Scratch root above.) Detection: wave 2 brought no new error (its R5, stability of integers, is classed as an ambiguity form defect D-1-3; its R4 is the same as wave 1's R3 consequence on abstract/conclusion): saturated after 2 waves.

## Chain digest

| ID | Statement before → after | Nature | Guards | Open suspects | Revision |
|---|---|---|---|---|---|
| F-1-1 | Lemma 3: i smallest at positions 1..i → i largest at positions n−i+1..n (proof rewritten) | statement fix + proof repair | test_F_1_1.py, test_F_1_1_text.py | — (Corollary 5 was confirmed false on its own, F-1-2) | r1 |
| F-1-2 | Corollary 5: pass i can start at i → pass i can stop at n−i+1 (proof rewritten) | statement fix | test_F_1_2.py, test_F_1_2_text.py | Algorithm 7 (F-1-3, confirmed false, fix pending) | r2 |
| F-1-5 | Example 6: first pass gives (1,3,2) → pass continues, returns (1,2,3) | statement fix | test_F_1_5.py, test_F_1_5_text.py | — | r3 |

## Iteration log

| Iter. | Detection waves | Saturated | Errors detected | Roots | Confirmed | Refuted | Resolved by their cause | Undecided | Blocked | Suspects | Form defects | Guards added | Corpus | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 3 | wave 3 brought nothing new (F-1-5 was found by the orchestrator after waves 1–2) | 5 | 2 (F-1-1, F-1-5) | 5 | 0 | 0 | 0 | 1 (F-1-4) | 1 added / 0 cleared / 1 confirmed (F-1-3) | 3 (1 fixed) | 7 files | 25 passed, 1 failed (lint D-1-1, red since baseline) | 1dbdbfa + report |

## Internal revisions

| Rev. | Commit | Error fixed | Errors fixed so far | Consequences not yet reassessed |
|---|---|---|---|---|
| r1 | (this commit) | F-1-1 | 1 | F-1-2, F-1-3 (suspects), F-1-4 |
| r2 | (this commit) | F-1-2 | 2 | F-1-3, F-1-4 |
| r3 | (this commit) | F-1-5 (+ D-1-2 typo) | 3 | F-1-3, F-1-4 (blocked on pending critical fix) |

## Cause graph — iteration 1

- F-1-1 → F-1-2: Corollary 5's proof applies Lemma 3, false as stated; the counterexample (2,3,1) is the same.
- F-1-2 → F-1-3: Algorithm 7's correctness rests on Corollary 5 (cited as "Corollary 8"); the run of Algorithm 7 on (2,3,1) is Corollary 5's counterexample.
- F-1-3 → F-1-4: abstract and conclusion state that Algorithm 7 sorts any list; their claim comes from F-1-3.

Initial root: F-1-1. Processing order: F-1-1, F-1-2, F-1-3, F-1-4.
Cycle: none.

## Errors

### F-1-1 — Lemma 3 states the wrong end of the list

- **Fingerprint**: [false statement] Lemma 3 — says the i smallest are at positions 1..i after i passes; the i largest are at the end — L = (2,3,1), i = 1
- **Origin**: reviewer (wave 1 R1, wave 2 R1)
- **Status**: FIXED
- **Type**: false statement; **Severity**: critical (adjudicator); not a "main result" (not a theorem, not named in abstract/conclusion), so not a critical fix to submit
- **Location**: §2 Lemma 3: "the i smallest elements of L occupy positions 1 to i, in increasing order"
- **Description**: a left-to-right pass carries the larger element right; small elements move left one place per pass. The proof step "moves left until it reaches position i" is invalid, and the induction is a sketch.
- **Causes**: root. **Consequences**: F-1-2 (via the proof of Corollary 5), then F-1-3, F-1-4
- **Probable cause**: direction of bubble sort inverted (dual statement)
- **Counterexample**: L = (2,3,1), i = 1; expected 1 at position 1, obtained (2,1,3). Script scratch/iter-1/adjudicator-F-1-1/t.py (`python3 …/t.py`), output "[2, 1, 3] / violations i=1: 86 / …"; re-run by the orchestrator, same output.
- **Evidence**: ad hoc
- **Adjudicator's verdict**: CONFIRMED; upstream cause none; Proposition 4 independent of Lemma 3
- **Impact**: Corollary 5, Algorithm 7 and its correctness, abstract and conclusion
- **Guards**: spec-guards/test_F_1_1.py (witness refutes original; fixed holds on witness, variants, near-case (1,3,2), exhaustive n ≤ 5 with repeated values, n = 6 permutations), spec-guards/test_F_1_1_text.py. Red first: text guard failed on the original document (1 failed, 5 passed); green after the fix (whole corpus: 8 passed, 1 failed = lint cross-reference, see D-1-1, red since the baseline).
- **Fix**: statement fix + proof repair: "i smallest … positions 1 to i" → "i largest … positions n − i + 1 to n, in increasing order, where n = |L|", proof rewritten as an induction with base case and step; commit r1
- **Links**: F-1-2 (same inverted direction)

### F-1-2 — Corollary 5 is false (pass i cannot start at i)

- **Fingerprint**: [false statement] Corollary 5 — the i-th pass can start at i without changing the output; positions 1..i−1 are not final — L = (2,3,1)
- **Origin**: reviewer (wave 1 R2, wave 2 R2)
- **Status**: FIXED
- **Type**: false statement; **Severity**: critical (adjudicator); not a main result (not in abstract/conclusion), so not a critical fix to submit
- **Location**: §2 Corollary 5: "the i-th pass can start at position i instead of position 1, without changing the output"
- **Causes**: F-1-1 (proof applied the false Lemma 3). **Consequences**: F-1-3
- **Probable cause**: inverted direction inherited from F-1-1; with the fixed Lemma 3 the statement is still false (the adjudicator, told nothing of the history, confirmed it against the fixed text)
- **Counterexample**: L = (2,3,1); Algorithm 2 gives (1,2,3), passes starting at i give (2,1,3); 98 permutations of sizes 2–5 differ. Script scratch/iter-1/adjudicator-F-1-2/t.py; output re-run by the orchestrator: "98 [...] / [1, 2, 3] [2, 1, 3]".
- **Evidence**: ad hoc
- **Adjudicator's verdict**: CONFIRMED (audit-bubble-sort-adjudicator-F-1-2, effort low, no escalation needed: executed evidence at the level allowed); upstream cause none
- **Impact**: Algorithm 7 and its correctness paragraph, abstract and conclusion
- **Guards**: spec-guards/test_F_1_2.py (witness, variants, near-case (3,1,2), exhaustive n ≤ 5 with repeated values, n = 6 permutations), test_F_1_2_text.py. Red first: text guard failed on the original (1 failed, 5 passed); green after the fix (corpus: 14 passed, 1 failed = lint cross-reference D-1-1, red since the baseline).
- **Fix**: statement fix: "can start at position i instead of position 1" → "can stop at position n − i + 1 instead of position n"; proof rewritten from Lemma 3 (positions n−i+2..n); commit r2
- **Links**: F-1-1

### F-1-3 — Algorithm 7 does not sort

- **Fingerprint**: [algorithm or complexity] Algorithm 7 / Correctness — passes from i to n do not sort — L = (3,2,1) returns (2,1,3)
- **Origin**: reviewer (wave 1 R3, wave 2 R2)
- **Status**: CONFIRMED — critical fix PENDING (Algorithm 7 is named in the abstract and the conclusion; no `--auto`, and no question channel in the audit session): to be presented to the user
- **Type**: false statement / algorithm; **Severity**: critical
- **Location**: §3 Algorithm 7 "make a pass from position i to position n" and Correctness "By Corollary 8, Algorithm 7 returns the same list as Algorithm 2, hence L sorted"
- **Causes**: F-1-2 (cited, as "Corollary 8" = dangling; Corollary 5 only shortens the END of a pass). **Consequences**: F-1-4
- **Counterexample**: L = (3,2,1): Algorithm 7 returns (2,1,3), not (1,2,3); also (2,3,1). Script scratch/iter-1/adjudicator-F-1-3/t.py; output re-run by the orchestrator: "([2, 1, 3], 3)". Algorithm 7 sorts only for n ≤ 2.
- **Evidence**: ad hoc
- **Adjudicator's verdict**: CONFIRMED (audit-bubble-sort-adjudicator-F-1-3, effort low; the evidence is executed, no escalation)
- **Guards**: spec-guards/test_F_1_3.py (witness, variants, near-case n = 2, exhaustive check of the PROPOSED fix, comparison count). No text guard yet: no fixed text. Green (the encoded original statement fails on the witness).
- **Proposed fix** (not applied): statement fix, "pass from position i to position n" → "pass from position 1 to position n − i + 1", correctness by Corollary 5 (count n(n−1)/2 unchanged); abstract ("passes start further and further into the list") and conclusion ("starts each pass where the part of the list already sorted ends") reworded to "shrinking end". Comparison and stability claims remain true for that variant.
- **Links**: F-1-2

### F-1-4 — Abstract and conclusion claim Algorithm 7 sorts any list, stably, with half the comparisons

- **Fingerprint**: [inconsistency] abstract and §4 — claim more than the body proves (Algorithm 7 as written does not sort) — L = (3,2,1)
- **Origin**: reviewer (wave 1 R3, wave 2 R4)
- **Status**: BLOCKED (by F-1-3): the critical fix stays pending with F-1-3; not adjudicated separately (its text is the same claim, and it would change with F-1-3's fix)

### F-1-5 — Example 6 gives the wrong result of the first pass

- **Fingerprint**: [wrong computed example] Example 6 — gives (1,3,2) as the result of the whole first pass; the pass goes on and returns (1,2,3) — L = (3,1,2)
- **Origin**: orchestrator's own reading while checking the baseline text (missed by both reviewers of waves 1 and 2); submitted to a fresh adjudicator like any other finding
- **Status**: FIXED
- **Type**: false statement (computed example); **Severity**: minor
- **Location**: §2 Example 6: "the first pass compares 3 and 1 and swaps them, which gives (1, 3, 2)"
- **Causes**: root. **Consequences**: none (no other result uses the example)
- **Counterexample**: L = (3,1,2), one pass from 1 to 3 → (1,2,3). Script scratch/iter-1/adjudicator-F-1-5/t.py; output re-run: "after comparison at j= 1 [1, 3, 2] / after comparison at j= 2 [1, 2, 3]".
- **Evidence**: ad hoc
- **Adjudicator's verdict**: CONFIRMED (audit-bubble-sort-adjudicator-F-1-5, effort medium: minor, ad hoc level)
- **Guards**: spec-guards/test_F_1_5.py, test_F_1_5_text.py. Red first: text guard failed on the original wording (1 failed, 4 passed); green after the fix.
- **Fix**: statement fix: added "; it then compares 3 and 2 and swaps them, so the pass returns (1, 2, 3)"; commit r3

## Form defects

- D-1-1 — cross-reference — §3 Correctness — "Corollary 8" → the corollary the correctness argument actually uses (to settle after F-1-2/F-1-3, since the argument is rewritten) — lint rule test_cross_references_resolve (red now)
- D-1-2 — typo — §3 Correctness — "comparisns" → "comparisons" — FIXED (r3) — lint rule test_known_misspellings_absent
- D-1-3 — ambiguity — Proposition 4 — stability is meaningless on lists of integers (equal integers are indistinguishable) — clarify without changing meaning (e.g. elements tracked by identity) — judged style-level, not an error: no counterexample can exist


## Closing
- Outcome: Partial, needs decision (critical fix F-1-3/F-1-4 pending; 1 expected-red lint check, D-1-1).
- Question: not asked, `--keep` applies "Keep the worktree". Recommended would have been the same.
- Answer: Keep the worktree. State: suspended.
- Audit session pid 21764, session <session> (not recorded earlier in the header).
- Results folder: SpecAudit-20261011_075706/
