# Register and guard formats

## Register header (`spec-audit/<slug>/register.md`)

```markdown
# Audit register — <document>

- Document(s): <paths>
- Normative dependencies: <paths>
- Corpus: <directory>, runner: <command>, lint: `<python> <worktree>/<corpus>/<lint>.py` (absolute path; the command every "run the lint" copies)
- Launched by: <name> <e-mail> (<source: git | GIT_AUTHOR_* | system user | unknown>, <context: local | cloud session | CI | routine>); Resumed by: <same>, if a `--resume` came from someone else
- Launched: <YYYYmmdd_HHmmss>, local time, UTC<offset> (launch of `/spec-audit:start`; kept by `--resume`; names the results folder `SpecAudit-<YYYYmmdd_HHmmss>/`)
- Original repository: <path>, remote <URL | none>, branch <name>, head <hash>
- Worktree: <path>, branch audit/<stamp> (the stamp of the results folder), base <hash>; final commit <hash>, at closing (never merged by the audit)
- Scratch root: <worktree>-scratch/ (audit session) | <worktree>/spec-audit/<slug>/scratch/ (`--in-session`, listed in .git/info/exclude); every agent's scratch directory is under it
- Interpreter: <command> (the one phase 0, step 4, ran and saw print a Python 3 version: `python3`, or `python` where `python3` is missing or a stub; written `<python>` in the protocol and given to every agent); paths: native | POSIX (native on Windows: `C:/…`, from `cygpath -m`)
- Preflight: passed, attempt <n> of 3 | failed (<tool>, <command form>, <refusal>), attempt <n> of 3 (the attempt is written in both cases: a pass at attempt 2 means the launch was fixed once)
- Refusals: <n> (each in the agent table's row or the log: who, command, message, retried in which form, outcome)
- Parameters: max-passes = N, auto = yes/no, fail-fast = yes/no, pause-at = <N | session=N,week=N | off>, auto-resume = yes/no, model = <family or id>, version = <v> | latest (passed: `--model <value>`); the values in force, the latest resume's changes included
  - changed at resume <YYYY-MM-DD HH:MM> by <who>: <option> <old> → <new>[; …] (one line per resume that changed an option; a model change also says that the verdicts before it came from <old model>)
- Version convention: fix in place | new revision <name>
- Architecture: SPECAUDIT_ARCH.md, <commit | copied, sha256:…>; audited: <paths>, profile <name>; normative dependencies given: <paths | none>; warnings of `arch.py require` <or none>; artifacts that look like oracles but are not in it <or none>
- Architecture refusals: <n> (each: path, role, the step and the error whose fix touched it, refused by the hook or by `arch.py check`, restored; an error of the audit, listed in the report)
- Configuration: <.specaudit.md | .specaudit/config.md | none>, <commit | copied, sha256:…>; deprecated keys `profiles` / `normative` <used for: … | none>; answer to the tracking question if one was asked
- Session: <id>, state: running | stopping | suspended | suspended (launcher session deleted) | suspended (usage limit: session | week, resumes <time>) | suspended (account: <email> expected, <found or logged out> found) | closed
- Resumes: <n> automatic resumes after a usage limit (at most 5), each with its window and time
- Mode: audit session (pid <pid>, session <id>) | in-session
- Account: <email> (<organization>), configuration folder <path>, settled by question | `--account`, remembered for the project yes | no; or this session's account, <email> (`CLAUDE_CODE_USER_EMAIL`) or unknown (`--in-session`). Fixed for the whole audit: every resume and relaunch checks it (`account.py check`); a folder changed for the same account is recorded after it, `folder <old> → <new> (<date>)`

## Environment

Resources of the launcher's session, ignored by the audit: <plugins, skills, connectors, hooks; from `claude plugin list --json` and `claude mcp list`, or "not enumerable">.

Session history in the project: <folders found (`.forge/`…), tracked | untracked, and the answer: untracked and ignored | kept, ignored by the agents | worktree used | continued>, or "none".

Oracles of the worktree, by strength, from the architecture's `Oracles` table (every command verified in the worktree at phase 0):

| Oracle | Kind | Path | Covers | Correspondence | Command | Guards |
|---|---|---|---|---|---|---|
| lean | formal | mechanization/ | Theorems 6.x, Lemmas 6.y | §6.6 table | `lake -d mechanization build` | mechanization/Guards/ |
| model | model | verification/model.py | rules of §4, Theorem 6.6 by bounded brute force | README | `python verification/run.py --seed 1` | — |
| guards | runner | verification/guards/ | the corpus | — | `python verification/guards/run_guards.py` | — |

Worktree autonomy, from the original directory <path>:

| Path | Nature | Action | Origin and SHA-256 (copies) |
|---|---|---|---|
| mechanization/.lake/packages | third-party cache | junction | — |
| sources/paper.pdf | input | copy | <path>, sha256:… |
| mechanization/.lake/build | build output | none, rebuilt | — |

## Agents

Every agent launched, in launch order, one at a time: a row is `done` (or `stopped`) before the next one is `running`. Its scratch directory holds its scripts, their outputs and, in the audit session, its journal (`prompt.md`, `journal.jsonl`, `result.md`, written by hooks), so that a replacement can reuse them. `Revision` is `git rev-parse --short HEAD` at its launch, the documents having no uncommitted change: the exact text it read.

| Name | Role | Error or wave | Effort | Revision | Scratch | State |
|---|---|---|---|---|---|---|
| audit-<slug>-reviewer-i1-w1-a | reviewer | iteration 1, wave 1, full | usual \| medium \| low; escalated from <effort> (<trigger>) | `4a55898` | <scratch>/iter-1/reviewer-a | pending \| running \| done \| stopped \| replaced by <name> |

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

## Hypothesis discharge — iteration <k>

`select`: <edges> edges, <n> stated, <n> from the cache, <n> to probe (`--strongest <level>`).

Probes of phase 1, then the re-probes after each fix (`references/discharge.md`, "Re-probe after a fix"), each on the revision it was launched on.

| Edge | User → used | Hypothesis | Probe | Revision | Verdict | Level | Lifted to | Finding | Edge status |
|---|---|---|---|---|---|---|---|---|---|
| E-3 | Proposition 3 → Lemma 2 | 0 ≤ x | audit-<slug>-probe-E-3 | `4a55898` | RED | ad hoc | Theorem 4 | F-1-2, F-1-3 | red → needed |

## Errors

## Form defects
```

## Error entry

```markdown
### F-<iteration>-<n> — <short title>

- **Fingerprint**: [type] object — defect — witness
- **Origin**: reviewer (R…, wave …) | suspect (uses F-…) | probe (E-…) | probe (lifted from E-…)
- **Status**: DETECTED | BLOCKED (by F-…) | CONFIRMED | REFUTED | UNDECIDED | FIXED | RESOLVED (by F-…) | ESCALATED | RECURRENCE
- **Type**: false statement | incomplete proof | insufficient scoping | definition | algorithm or complexity | inconsistency
- **Severity**: critical (false result) | major (incomplete proof, missing hypothesis) | minor (local imprecision)
- **Location**: section, and exact quote of the passage (two lines at most), as of the last freshness check (4.0): re-quoted, with the revision, when a fix changed it
- **Description**: what is wrong, and why
- **Causes**: F-… (with the justification of the edge), or "root"
- **Consequences**: F-…
- **Probable cause**: implicit hypothesis, forgotten edge case, neighboring result copied over, overloaded notation…
- **Counterexample(s)**: minimal instance, result expected according to the text, result obtained, path of the script and its command (a counterexample is always executed, never evaluated by hand)
- **Evidence**: formal (<oracle>) | model (<oracle>) | ad hoc
- **Adjudicator's verdict**: summary, and reason for rejection if any; misleading wording, if flagged
- **Verdicts**: every verdict on this entry, in order, each with the revision its agent was launched on: `` `<sha>` <CONFIRMED | REFUTED | UNDECIDED | RESOLVED (freshness) | user decision> (<agent name or "user">) ``, separated by semicolons (a first confirmation, an escalation, a reassessment, a user decision); every sha is a commit of `audit/<stamp>`
- **Impact**: dependent results and passages (from the inventory)
- **Guards**: paths in the corpus; red state before the fix, green after
- **Fix**: nature (statement fix | scoping addition | proof completion); before → after; commit
- **Links**: errors of the same class
```

A suspect entry starts with its origin, its location (the result, and what it uses from F-…), its cause and the status BLOCKED; its fingerprint, type, counterexample and fix are filled in only if it is confirmed.

Identifiers are never reassigned. A refuted error stays in the register: it is what makes it possible to discard the same false positive in the next pass.

## Index of the audits (`SPECAUDITS.md`, at the root of the project)

Every audit launched in the project has an entry, from its launch: a row of the summary table, linked to a section of its own. Both are kept newest first. The entry's identifier is the results folder's name, `SpecAudit-<stamp>`, reserved at launch, so the row, the section, the folder, the attestation tag and the audit's branch, `audit/<stamp>`, all carry the same name.

```markdown
# SpecAudit index

Every audit launched in this project, newest first. Each entry is written at launch and updated when the audit ends, however it ends; an entry still RUNNING whose audit is no longer running was interrupted without a chance to say so (`--resume` or `/spec-audit:stop` updates it).

| Date | Audited object | Launched by | Result |
|---|---|---|---|
| [2026-10-11 00:28:27](#specaudit-20261011_002827) | `docs/spec/` (folder, 3 documents) | Ada Lovelace | FINISHED — Partial, needs decision |
| [2026-10-10 21:37:08](#specaudit-20261010_213708) | `selection.md` | Alan Turing | INTERRUPTED — suspended |
| [2026-09-01 10:00:15](#specaudit-20260901_100015) | `selection.md` | Alan Turing | FINISHED — Success |

## SpecAudit-20261011_002827

Audit of the three documents of `docs/spec/` (`merge.md`, `bounds.md`, `index.md`), launched by Ada Lovelace from a local session on `main`. It confirmed five errors and fixed four, each with its guards; the fifth, the main theorem's bound in the abstract, is a critical fix that awaits a decision, and convergence was not established in one iteration. The fixes are on the branch `audit/20261011_002827`, kept and not merged: merging it is the user's decision.

| | |
|---|---|
| Launched | 2026-10-11 00:28:27 UTC+0200, by Ada Lovelace <ada@example.org> (git, local session) |
| Audited object | `docs/spec/` (folder, 3 documents) |
| Base | `4a55898` on `main` |
| Result | FINISHED — Partial, needs decision |
| Closing | Keep the branch |
| Branch | `audit/20261011_002827`, final commit `9c1e2f7`, kept, not merged |
| Errors confirmed / fixed | 5 / 4 |
| Fixed copy | no (a critical fix is pending) |
| Consumption | 6.41 M tokens, $2.93, 3 points of the week window |
| Results folder | [SpecAudit-20261011_002827/](SpecAudit-20261011_002827/README.md) |
| Attested | no |

## SpecAudit-20261010_213708

Audit of `selection.md`, stopped by Alan Turing during iteration 1 and suspended: two errors fixed up to internal revision r2, the others not yet handled. `--resume` continues it from that revision.

| | |
|---|---|
| Launched | 2026-10-10 21:37:08 UTC+0200, by Alan Turing <alan@example.org> (git, local session) |
| Audited object | `selection.md` |
| Base | `f87c1e4` on `main` |
| Result | INTERRUPTED — suspended |
| Results folder | none yet; worktree `SpecAudit-audit-selection`, branch `audit/20261010_213708` |
| Attested | — |
```

**Result**: a status, how the audit ended, then a detail, what it found or why it stopped:
- `RUNNING`, from the launch until the audit ends, and again during a `--resume`;
- `FINISHED — <outcome>`: the audit ran to its end; the outcome is the one of closing, 8.1 (`Success`, `Partial, to continue`, `Partial, needs decision`, `Failure` with its reason: causal loop, recurrence, oscillation, non-convergence);
- `INTERRUPTED — suspended | ended at last revision | cancelled`: stopped on request (8.9);
- `FAILED — preflight | execution error`: the audit could not run, or stopped on an error; the section says which tool or step, and where the archive is (8.4.1).

**Section**: one paragraph that a reader who was not there can act on (what was audited, by whom, what was found, fixed and left open, what to do next), then the table. Its `Consumption` row, written at closing, is the `index` value of `consumption.py --json` (`references/launch.md`, step 6): the total tokens, the cost and the audit's share of the week window, whose details and caveats are in the report; `not measured (--in-session)` with `--in-session`. Write the paragraph in plain words, and keep the details in the table and in the results folder.

**Rules**: an entry is written by its own audit and by nothing else, except the "Attested" cell: `—` while there is no results folder to attest, `no` from the closing that builds the folder (the closing sets it), and after that only `/spec-audit:attest --update` changes it, from what it verified (a signed tag `specaudit/<id>`). Audits launched side by side in the same repository write this file at the same moments (launch, closing), so every write, by any step, follows **Writing the index** below. Insert a new entry at the top of the table and before the first section, and commit only `SPECAUDITS.md` (with the results folder at closing). "Launched by" in the table is the name only; the e-mail is in the section. The audited object is written as given on the command line, a file or a folder; for a folder, with its number of documents.

**Writing the index.** A re-read followed by a write of the whole file is not enough: between the two, another audit may write its entry, and the stale copy erases it; and done by hand, the lock, the read, the write, the check and the commit are steps a session can chain or reorder, which has let one audit erase another's entry. Every write of `SPECAUDITS.md`, at launch, closing, stop or failure, therefore goes through one script, which does them all in order under the lock:

1. Write the audit's whole entry, as it must read after this write, to a file of its own (`spec-audit/<slug>/index-entry.md` in the worktree, or the scratch root): its row, a blank line, then its section, both carrying its identifier `SpecAudit-<stamp>` from the register's `Results folder`.
2. Run `<python> ${CLAUDE_SKILL_DIR}/references/index.py "<original repository>" --entry <that file> --message "<commit message>"`, with `--add <results folder>` at closing, or `--no-commit` when the project rules forbid the commit, and `--register <register>` when the entry file is not next to the register (in the scratch root). It also records the audit in `~/.specaudit/audits.json`, the index of every audit on the machine that a monitor reads (best effort: it only points to the register, which stays the audit's one source of truth, and a record that cannot be written changes nothing). It takes the lock (`SPECAUDITS.md.lock`, an empty folder next to the index), reads the file under it or creates it, replaces your entry or inserts it newest first, checks that every other entry is unchanged, commits, and unlocks whatever happens.
3. Read its exit code: 0, written and committed; 1, the lock or the commit could not be had (retry once after a minute, then record it in the register and go on); 2, your entry is malformed or another entry would have changed, and nothing was written: fix the entry file, never the index by hand.

Never edit `SPECAUDITS.md` yourself: only `index.py` writes it, and `/spec-audit:attest --update` its "Attested" cells, under the same lock.

## Chain digest (in the register, after the agent table)

One line per error once it is FIXED or RESOLVED, written at that moment. It is what the orchestrator carries along the chain; the full entry stays below, reread only when an agent's result concerns it.

```markdown
| ID | Statement before → after | Nature | Guards | Open suspects | Revision |
|---|---|---|---|---|---|
| F-1-1 | Lemma 3: \|P_k(L)\| = k → = min(k, \|L\|) | statement fix | test_F_1_1.py, test_F_1_1_text.py | Corollary 5, Algorithm 7 | r1 |
| F-1-2 | Corollary 5: … → … | statement fix | test_F_1_2.py, test_F_1_2_text.py | — | r2 |
```

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
