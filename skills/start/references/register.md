# Register and guard formats

## Register header (`spec-audit/<slug>/register.md`)

```markdown
# Audit register — <document>

- Document(s): <paths>
- Normative dependencies: <paths>
- Corpus: <directory>, runner: <command>
- Launched by: <git user.name> <git user.email> | <system user> (no git identity); Resumed by: <same>, if a `--resume` came from someone else
- Launched: <YYYYmmdd_HHmm>, local time, UTC<offset> (launch of `/spec-audit:start`; kept by `--resume`; names the results folder `SpecAudit-<YYYYmmdd_HHmm>/`)
- Original repository: <path>, remote <URL | none>, branch <name>, head <hash>
- Worktree: <path>, branch audit/<slug>, base <hash>
- Parameters: max-iter = N, auto = yes/no, model = <family or id>, version = <v> | latest (passed: `--model <value>`)
- Version convention: fix in place | new revision <name>
- Configuration: <.specaudit.md | .specaudit/config.md | none>, <commit | copied, sha256:…>; profile <name>; answer to the tracking question if one was asked
- Session: <id>, state: running | stopping | suspended | closed
- Mode: audit session (pid <pid>, session <id>) | in-session

## Environment

Resources of the launcher's session, ignored by the audit: <plugins, skills, connectors, hooks; from `claude plugin list --json` and `claude mcp list`, or "not enumerable">.

Session history in the project: <folders found (`.forge/`…), tracked | untracked, and the answer: untracked and ignored | kept, ignored by the agents | worktree used | continued>, or "none".

Oracles of the worktree, by strength (every command verified in the worktree at phase 0):

| Oracle | Kind | Path | Covers | Correspondence | Command |
|---|---|---|---|---|---|
| lean | formal | mechanization/ | Theorems 6.x, Lemmas 6.y | §6.6 table | `lake build` |
| model | model | verification/model.py | rules of §4, Theorem 6.6 by bounded brute force | README | `python verification/run.py --seed 1` |
| guards | runner | verification/guards/ | the corpus | — | `python verification/guards/run_guards.py` |

Worktree autonomy, from the original directory <path>:

| Path | Nature | Action | Origin and SHA-256 (copies) |
|---|---|---|---|
| mechanization/.lake/packages | third-party cache | junction | — |
| sources/paper.pdf | input | copy | <path>, sha256:… |
| mechanization/.lake/build | build output | none, rebuilt | — |

## Agents

Every agent launched, in launch order. Its scratch directory holds its scripts, their outputs and its `progress.md` (sections read or method step reached, candidate errors or verdict in progress, scripts and outputs), so that a replacement can reuse them.

| Name | Id | Role | Error or wave | Scratch | State |
|---|---|---|---|---|---|
| audit-<slug>-reviewer-i1-w1-a | <agent id returned at launch, for a background agent> | reviewer | iteration 1, wave 1, full | <scratch>/iter-1/reviewer-a | running \| done \| stopped \| replaced by <name> |

## Iteration log

| Iter. | Detection waves | Saturated | Errors detected | Roots | Confirmed | Refuted | Resolved by their cause | Undecided | Blocked | Suspects | Form defects | Guards added | Corpus | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Suspects: added / cleared / confirmed. They are counted only in this column, so that they inflate neither the errors detected nor those resolved by their cause.

## Internal revisions

One commit per fixed error, plus the end-of-iteration commits; each one is marked incomplete until closing.

| Rev. | Commit | Error fixed | Errors fixed so far | Consequences not yet reassessed |
|---|---|---|---|---|

## Cause graph — iteration <k>

"Cause → consequence" edges, one per line, each one justified:

- F-k-1 → F-k-4: Proposition 4.6 applies Lemma 4.3, false for k > n; its counterexample is the same.
- F-k-1 → F-k-7: …
- F-k-1 → F-k-9 (suspect): Theorem 5.2 uses F-k-1, confirmed false as stated.

Initial roots: F-k-1, F-k-2. Processing order: F-k-2, F-k-1 (inventory dependencies).
Cycle: none | <errors of the cycle> → stop.

## Errors

## Form defects
```

## Error entry

```markdown
### F-<iteration>-<n> — <short title>

- **Fingerprint**: [type] object — defect — witness
- **Origin**: reviewer (R…, wave …) | suspect (uses F-…)
- **Status**: DETECTED | BLOCKED (by F-…) | CONFIRMED | REFUTED | UNDECIDED | FIXED | RESOLVED (by F-…) | ESCALATED | RECURRENCE
- **Type**: false statement | incomplete proof | insufficient scoping | definition | algorithm or complexity | inconsistency
- **Severity**: critical (false result) | major (incomplete proof, missing hypothesis) | minor (local imprecision)
- **Location**: section, and exact quote of the passage (two lines at most)
- **Description**: what is wrong, and why
- **Causes**: F-… (with the justification of the edge), or "root"
- **Consequences**: F-…
- **Probable cause**: implicit hypothesis, forgotten edge case, neighboring result copied over, overloaded notation…
- **Counterexample(s)**: minimal instance, result expected according to the text, result obtained, path of the script and its command (a counterexample is always executed, never evaluated by hand)
- **Evidence**: formal (<oracle>) | model (<oracle>) | ad hoc
- **Adjudicator's verdict**: summary, and reason for rejection if any; misleading wording, if flagged
- **Impact**: dependent results and passages (from the inventory)
- **Guards**: paths in the corpus; red state before the fix, green after
- **Fix**: nature (statement fix | scoping addition | proof completion); before → after; commit
- **Links**: errors of the same class
```

A suspect entry starts with its origin, its location (the result, and what it uses from F-…), its cause and the status BLOCKED; its fingerprint, type, counterexample and fix are filled in only if it is confirmed.

Identifiers are never reassigned. A refuted error stays in the register: it is what makes it possible to discard the same false positive in the next pass.

## Index of the results folders (`SPECAUDITS.md`, at the root of the project)

```markdown
# SpecAudit index

Results of the audits of this project, newest first: one row per results folder, added at closing by `/spec-audit:start`. Rows are never rewritten.

| Results folder | Launched | Launched by | Audited source | Base | Outcome | Closing | Errors confirmed / fixed | Fixed copy |
|---|---|---|---|---|---|---|---|---|
| [SpecAudit-20261010_2137](SpecAudit-20261010_2137/README.md) | 2026-10-10 21:37 UTC+0200 | Ada Lovelace | `docs/spec/` (folder, 3 documents) | `831ef36` on `main` | Partial, needs decision | Keep | 5 / 4 | no |
| [SpecAudit-20260901_1000](SpecAudit-20260901_1000/README.md) | 2026-09-01 10:00 UTC+0200 | Alan Turing | `selection.md` | `f87c1e4` on `main` | Success | Accept | 3 / 3 | `selection.fixed.md` |
```

"Launched by" is the name only (git `user.name`, or the system user); the e-mail stays in the folder's README, which keeps the index short. The audited source is written as given on the command line, a file or a folder; for a folder, with its number of documents (the list is in the folder's README and register).

## Corpus error entry

```markdown
### G-<iteration>-<n> — <guard file> — <short title>

- **Guard**: path; error it guards (F-…), or project test (oracle table)
- **Suspicion**: red on a fix considered valid | green on the original | NO TEXT CHECK | red at baseline; what was observed (command, output)
- **Status**: OPEN | FAULTY | FAITHFUL | UNDECIDED | ESCALATED
- **Adjudicator**: agent name; verdict and reason; defect (too strict | badly encoded | empty)
- **Settlement**: new guard (path, red-first result on the original, green result) | regression rule applied to F-… | escalated; for a project test, reported to the author
- **Coverage**: cases lost by the replacement, and why the old guard was wrong on them, or "none"
- **Commit**
```

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

## Text guard (Python example)

A text guard reads the document through `SPEC_DOCS`, a JSON map from the document's path in the project to the file to read; without it, the path itself is read, from the directory the runner starts in. The replay of a results folder sets it to the original or to the fixed copy.

```python
# Text guard F-2-3 — the fixed wording of Proposition 4.2 is in the document, the original one is not
import json, os
from pathlib import Path

def doc(path):
    return Path(json.loads(os.environ.get("SPEC_DOCS", "{}")).get(path, path)).read_text(encoding="utf-8")

def test_F_2_3_text():
    text = doc("spec/merge.md")
    assert "<original wording, exact>" not in text
    assert "<fixed wording, exact>" in text
```

## Manifest of a results folder (`resources/manifest.json`)

```json
{
  "documents": {"spec/merge.md": {"source": "source/spec/merge.md", "fixed": "spec/merge.fixed.md"}},
  "guards": [
    {"error": "F-2-3", "file": "resources/corpus/test_F_2_3.py", "text": false,
     "command": ["pytest", "-q", "-p", "no:cacheprovider", "resources/corpus/test_F_2_3.py"]},
    {"error": "F-2-3", "file": "resources/corpus/test_F_2_3_text.py", "text": true,
     "command": ["pytest", "-q", "-p", "no:cacheprovider", "resources/corpus/test_F_2_3_text.py"]},
    {"error": "lint", "file": "resources/corpus/test_lint.py", "text": true,
     "command": ["pytest", "-q", "-p", "no:cacheprovider", "resources/corpus/test_lint.py"]}
  ]
}
```

Commands run from the root of the results folder. `"fixed"` is `resources/<name>.partial<ext>` when an error stays open. The lint is a text check of the whole document: on the original it goes red if a form defect was fixed.

## Guard file (Lean example, for a formal oracle)

The module is added to the build target, so that replaying the corpus is `lake build`. The witness refutes the original statement as it is mapped in the development (correspondence table), and the fixed statement is re-proved or decided on the same instances. `native_decide` may find a witness; the recorded guard uses `decide`, `simp` or a proof.

```lean
-- Guard F-2-3 — [false statement] bound of the partial merge — ignores the case k > n — n = 2, k = 3
-- Original statement: <quote>; formal counterpart: Merge.partialBoundStatement (correspondence table §6.6)
-- Fixed statement:    <quote> (scoping addition: k ≤ n); formal counterpart: Merge.partialBoundStatement'
-- Consequences covered: F-2-5 (Proposition 4.6), resolved by this fix.
import Project.Merge

namespace Guards.F_2_3

def witness : Merge.Instance := ⟨2, 3, [1, 2]⟩
def variants : List Merge.Instance := [⟨0, 1, []⟩, ⟨1, 1, [1]⟩]
def nearCase : Merge.Instance := ⟨3, 2, [1, 2, 3]⟩

/-- Red first: the original statement fails on the witness. -/
theorem original_refuted : ¬ Merge.partialBoundStatement witness := by decide

/-- Green: the fixed statement holds on the witness, the variants and the near-case. -/
theorem fixed_holds : (witness :: nearCase :: variants).all Merge.partialBoundStatement' = true := by decide

/-- The near-case is where the original statement is true as well: against over-correction. -/
theorem near_case_original : Merge.partialBoundStatement nearCase := by decide

/-- Bounded check of the fixed statement on every instance of size at most 4. -/
theorem fixed_bounded : ∀ i ∈ Merge.Instance.upTo 4, Merge.partialBoundStatement' i := by decide

/-- Consequence: Proposition 4.6 holds on the cause's witness. -/
theorem prop_4_6_on_witness : Merge.prop46Statement witness := by decide

end Guards.F_2_3
```
