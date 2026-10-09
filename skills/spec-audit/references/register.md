# Register and guard formats

## Register header (`spec-audit/<slug>/register.md`)

```markdown
# Audit register — <document>

- Document(s): <paths>
- Normative dependencies: <paths>
- Corpus: <directory>, runner: <command>
- Original repository: <path>, branch <name>, head <hash>
- Worktree: <path>, branch audit/<slug>, base <hash>
- Parameters: max-iter = N, auto = yes/no
- Version convention: fix in place | new revision <name>

## Iteration log

| Iter. | Detection waves | Saturated | Errors detected | Roots | Confirmed | Refuted | Resolved by their cause | Undecided | Blocked | Form defects | Guards added | Corpus | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Cause graph — iteration <k>

"Cause → consequence" edges, one per line, each one justified:

- F-k-1 → F-k-4: Proposition 4.6 applies Lemma 4.3, false for k > n; its counterexample is the same.
- F-k-1 → F-k-7: …

Initial roots: F-k-1, F-k-2. Processing order: F-k-2, F-k-1 (inventory dependencies).
Cycle: none | <errors of the cycle> → stop.

## Errors

## Form defects
```

## Error entry

```markdown
### F-<iteration>-<n> — <short title>

- **Fingerprint**: [type] object — defect — witness
- **Status**: DETECTED | BLOCKED (by F-…) | CONFIRMED | REFUTED | UNDECIDED | FIXED | RESOLVED (by F-…) | ESCALATED | RECURRENCE
- **Type**: false statement | incomplete proof | insufficient scoping | definition | algorithm or complexity | inconsistency
- **Severity**: critical (false result) | major (incomplete proof, missing hypothesis) | minor (local imprecision)
- **Location**: section, and exact quote of the passage (two lines at most)
- **Description**: what is wrong, and why
- **Causes**: F-… (with the justification of the edge), or "root"
- **Consequences**: F-…
- **Probable cause**: implicit hypothesis, forgotten edge case, neighboring result copied over, overloaded notation…
- **Counterexample(s)**: minimal instance, result expected according to the text, result obtained, path of the script
- **Adjudicator's verdict**: summary, and reason for rejection if any
- **Impact**: dependent results and passages (from the inventory)
- **Guards**: paths in the corpus; red state before the fix, green after
- **Fix**: nature (statement fix | scoping addition | proof completion); before → after; commit
- **Links**: errors of the same class
```

Identifiers are never reassigned. A refuted error stays in the register: it is what makes it possible to discard the same false positive in the next pass.

## Form defect entry

```markdown
- D-<iteration>-<n> — <typo | numbering | cross-reference | bibliography | ambiguity> — <location> — <before → after> — <source for the bibliography, or "to be checked"> — <lint rule added>
```

## Guard file (Python example, to adapt to the project's runner)

```python
# Guard F-2-3 — [false statement] bound of the partial merge — ignores the case k > n — n = 2, k = 3
# Original statement: <quote>
# Fixed statement:    <quote> (scoping addition: k ≤ n)
# Model: definitions of §2 of the document, encoded without reference to the fix.
# Consequences covered: F-2-5 (Proposition 4.6), resolved by this fix.
from fractions import Fraction

def original_statement(instance): ...
def fixed_statement(instance): ...

def test_F_2_3_original_refuted_by_witness():
    assert not original_statement(WITNESS)

def test_F_2_3_fixed_holds_on_witness_and_variants():
    for case in [WITNESS, *VARIANTS]:
        assert fixed_statement(case)

def test_F_2_3_near_case_where_original_is_true():
    assert original_statement(NEAR_CASE) and fixed_statement(NEAR_CASE)

def test_F_2_3_fixed_exhaustive_on_bounded_domain():
    for case in domain(max_size=4):
        assert fixed_statement(case), case

def test_F_2_5_consequence_holds_on_cause_witness():
    assert proposition_4_6(WITNESS)
```
