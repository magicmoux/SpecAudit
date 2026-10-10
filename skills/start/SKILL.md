---
description: >-
  Iterative precision audit of a theoretical, technical or mathematical specification
  (manuscript, paper, proof, algorithm, protocol or format specification), run in a
  dedicated git worktree: complete cold detection by fresh agents with no history, sorting
  of errors into causal chains, fixing causes before their consequences (bottom-up),
  confirmation of each error by an executed counterexample, regression guards in a global
  test corpus, correction of statements, scoping and proofs, then of typos, bibliography,
  numbering and cross-references, and a new pass until convergence, budget exhaustion,
  recurrence of a fixed error or a causal loop. Ends with a multiple-choice question to the
  user (accept and merge, run another check, keep, abandon), the safest option being
  recommended, and the report brought back to the original session and branch in every case.
  Use whenever the user wants to proofread, check, audit, harden or make reliable a formal
  document, hunt for errors in theorems, lemmas, algorithms or proofs, or prepare a
  specification for submission or publication, even without saying "audit".
argument-hint: "<document> [--corpus <dir>] [--max-iter N] [--auto] [--resume] [--base <ref>] [--no-worktree] [--in-session] [--model <id>] [--keep]"
---

# Precision audit of a specification

An author cannot see their own blind spots, and a reviewer who knows the history reads what they expect to read. This skill therefore separates the roles: fresh reviewers who know nothing about the audit, an adjudicator who confirms or refutes each error, and you, the orchestrator, who keep the register, sort the errors, write the guards and make the fixes. Three principles guide everything else:

- **An unconfirmed error is not an error.** Reviewers produce false positives, and fixing a correct statement damages the document as much as leaving a false one.
- **Fix a cause before its consequences.** Fixing a consequence first masks the cause, or compensates for it locally (a hypothesis added in the wrong place).
- **An error fixed without a guard will come back.** Every fix leaves a test in the corpus that would fail if the error reappeared.

## What counts as an error

An **error** is a defect in the content specific to the document's domain (logical, mathematical, algorithmic, theoretical):

- a false statement (a counterexample exists);
- an invalid or incomplete proof;
- insufficient scoping: missing hypothesis, context or domain of application not restricted, edge case not handled;
- a definition that is inconsistent, ill-founded, or ambiguous enough to change a result;
- an algorithm that does not meet its specification, termination not guaranteed, a wrong complexity;
- two results that contradict each other, or an abstract, introduction or conclusion that claims more than the body proves;
- a wrong formula or computed example, even from a typo, since the meaning changes.

Only errors follow the full protocol: cause graph, counterexample, guards, bottom-up fixing.

**Form defects** (typo outside formulas, numbering, cross-reference, bibliography entry) are not errors in the sense of this protocol. They follow the editorial track (phase 5), without counterexample or causal chain. Style preferences are discarded.

## Parameters

- `<document>`: the audited file or files.
- `--corpus <dir>`: the global guard corpus. By default, the project's existing verification corpus if there is one (follow its conventions), otherwise `spec-guards/` at the root.
- `--max-iter N`: maximum number of iterations (default 5).
- `--auto`: also apply critical fixes without pausing (see 4.3).
- `--resume`: resume an interrupted or suspended audit from its register, in its existing worktree, from its last internal revision (4.3).
- `--base <ref>`: starting branch or commit of the worktree (default: `HEAD` of the current repository).
- `--no-worktree`: work in the current directory, without a worktree, when it is already isolated for the audit.
- `--in-session`: run the orchestrator in the current session. By default the audit runs in a session of its own (phase 0, step 6), started in the worktree with the file tools, Bash, the two agents and the project's oracles, and none of the plugins, skills, connectors, hooks or memory of your session.
- `--model <id>`: model of the audit session, which its agents inherit (`model: inherit` in `agents/`): an alias (`opus`, `sonnet`) or a full model id. Default: the model of your session, as your context names it. With `--in-session`, the agents inherit your session's model and the option is ignored.
- `--keep`: at closing, ask no question and keep the worktree; only the report is brought back (phase 8).

## Roles

| Role | Who | Sees | Writes |
|---|---|---|---|
| Launcher | you | your session, the original repository, the register | worktree and register (phase 0, steps 1 to 6), stop (8.9), closing (phase 8) |
| Orchestrator | the audit session (phase 0, step 6), or you with `--in-session` | everything in the worktree: register, corpus, oracles, git history | document, corpus, register |
| Reviewer | `spec-reviewer` agent, fresh for each wave | the document and its normative dependencies, nothing else | nothing, outside its scratch directory |
| Adjudicator | `spec-adjudicator` agent, fresh for each error | one error and the document | nothing, outside its scratch directory |

Installed in `~/.claude/agents/`, these agents are called `spec-reviewer` and `spec-adjudicator`; installed as a plugin, `spec-audit:spec-reviewer` and `spec-audit:spec-adjudicator`. If they are not available, launch a fresh general-purpose agent, giving it the content of `spec-reviewer.md` or `spec-adjudicator.md` as instructions (in `~/.claude/agents/`, or in the plugin's `agents/` folder). Never use a "fork" agent: it would inherit the conversation, hence the history. Give every agent a name at launch, `audit-<slug>-<role>-<id>` (for example `audit-selection-adjudicator-F-1-3`): the name is what lets the audit stop it (8.9).

In the audit session, the agents are passed at launch (`--agents`, phase 0, step 6) from the plugin's `agents/` folder, under the same names.

## Phase 0 — Preparation (once)

1. **Project rules.** Read `CLAUDE.md`, the project's conventions and memory: they take precedence over this skill (attribution headers, document versioning, push policy, scope of the theory, status of proofs).
2. **Version convention.** Does the project fix the document in place, or create a new revision (new file, history section)? Follow the convention; if it is unclear, ask once.
3. **Dedicated worktree.** Unless `--no-worktree` is given, the whole audit runs in a git worktree created for it: the document is modified there, the corpus grows there, the commits stay there, without touching the user's directory or the sessions working in it in parallel.
   - `<slug>`: the document name without extension, in lowercase ASCII, words separated by hyphens.
   - Record the path of the original repository, its current branch and its head commit, and note them in the register: closing (phase 8) depends on them.
   - Record `git status` of the current repository. If the document, its normative dependencies or the corpus have uncommitted changes, they will not exist in the worktree: ask the user whether to audit the committed version or to commit first. Do not use `git stash`, which is shared between all worktrees.
   - Name the branch `audit/<slug>` and the directory `<parent of the repository root>/<repository name>-audit-<slug>`. If either already exists outside `--resume`, add a suffix `-2`, `-3`…
   - Create it: `git worktree add "<directory>" -b audit/<slug> <base>`, where `<base>` is `--base` or `HEAD`. With `--resume`, find it instead with `git worktree list`.
   - From now on, all commands run in the worktree (absolute paths, or `git -C "<directory>"`), and agents receive absolute paths in the worktree.
   - Files that git does not track (ignored caches, build outputs, PDF sources, environments) are not there: step 4 decides what the worktree takes from the original directory. Once the audit has started, nothing is read in the original directory any more.
   - With `--no-worktree`, work in place, but record `git status`: other sessions may be working in parallel, and their changes are not yours.
   - Outside a git repository, ask whether to initialize one: without git, there is neither isolation nor commits.
   - In all cases, commit only your files and never push.
4. **Environment.** The audit uses the worktree, the file tools, Bash, the two agents and the project's own oracles, nothing else. Establish that; step 5 records it in the register (format in `references/register.md`):
   - **Session inventory.** List what your session exposes and that the audit ignores: plugins and skills (`claude plugin list --json`, or the list in your context), connectors (`claude mcp list`), hooks. Record them as *ignored*. Never invoke a skill or a connector during the audit, in any mode: they bring context the reviewers must not have, and they are not reproducible.
   - **Oracles.** Find, in the worktree, every artifact that can decide statements of the document: a mechanized development (Lean: `lakefile.toml` or `lakefile.lean` and `lean-toolchain`; Coq, Isabelle, Agda likewise), a reference model or brute-force checker (`verification/`, `model`, scripts the document names), a test runner (`pytest`, `cargo test`, `mvn test`, a `run_*.py`), engines reachable from the runner (SQLite, DuckDB). For each one, record its kind (formal, model, runner), its path, the statements or sections it covers (from the document's own correspondence table when it has one, for instance a "Lean theorems / results" table, otherwise from its README), and its command. Run the command once in the worktree: an oracle whose command does not run is not an oracle. Order the table by strength: formal, then model, then runner. This table goes to every reviewer (phase 1) and every adjudicator (4.1).
   - **Worktree autonomy.** `git -C "<original repository>" status --ignored --porcelain` lists what git ignores. For each ignored path an oracle needs, by nature:
     - *third-party cache* (`.lake/packages`, `node_modules`, a venv, a vendored dependency): **share** it from the original directory by a junction or symbolic link (`mklink /J` on Windows, `ln -s` elsewhere); it is read, not rebuilt, and the original is untouched;
     - *input the project does not version* (PDF sources, data files, `.env`): **copy** it once into the worktree and record its origin and SHA-256 in the register, so that the audit stays replayable and the report says what it ran on;
     - *build output of the project itself* (`.lake/build`, `target/`, `__pycache__`, `dist/`): **nothing**; the worktree rebuilds it from its own sources, which is what makes the baseline probative. A build output copied from the original directory could come from sources that differ from the commit audited.
   - **Stop and ask.** If an oracle cannot run from the worktree alone (toolchain missing, cache absent and too large to share, runner not installed), stop and ask the user, with AskUserQuestion, what to install or share. Never replace an oracle by a script of your own, and never start an audit whose baseline is not green from the worktree alone.
5. **Register.** Create `spec-audit/<slug>/register.md` (format in `references/register.md`), or reread it with `--resume`. It is the audit's memory: it must survive a context compaction, so update it after each step, not at the end. Record in it this session, `${CLAUDE_SESSION_ID}`, and the state `running`: only the session that launched the audit may stop it (8.9), because only it knows the step in progress and the process or agents running.
   - Record the mode (`audit session`, with its process id and session id once launched at step 6, or `in-session`), the session inventory, the oracle table and the autonomy actions of step 4.
   - Name this session `[AUDIT] <slug>` if a tool lets you rename it (Claude desktop app); otherwise suggest once that the user run `/rename [AUDIT] <slug>`. The name tells the user which session to stop the audit from.
   - With `--resume`: if the register's state is `running` or `stopping` and its session is not this one, the audit may still be running there: ask the user to confirm that it is not before taking over, then record this session. The last commit of the audit branch is always a verified state (an internal revision, 4.3); the uncommitted changes after it were never verified. Save those to the document and the corpus, untracked files included, as `spec-audit/<slug>/in-flight-<YYYY-MM-DD>.patch`, restore the document and the corpus to the last commit, and redo the step in progress recorded in the register.
6. **Audit session.** Unless `--in-session` is given, the audit runs in a session of its own, so that nothing of your session (plugins, skills, connectors, hooks, memory, conversation) reaches it, and so that what it may run is exactly the oracle table. From the worktree:
   - Write in your scratch directory, regenerated at each launch and at each `--resume`: `protocol.md`, this skill followed by `references/register.md`, preceded by the line "You are the orchestrator of an audit prepared by its launcher: phase 0, steps 1 to 6, is done and recorded in the register; continue at step 7; launch no agent other than `spec-reviewer` and `spec-adjudicator`; never run phase 8, which the launcher does from your report"; and `agents.json`, the two agents of the plugin's `agents/` folder as the `--agents` format wants them (`description`, `prompt` = the body of the file, `tools`, `model`), under their names `spec-reviewer` and `spec-adjudicator`.
   - Build the Bash allow list from the oracle table: `Bash(git *)` and, per oracle, its runner only (`Bash(python *)`, `Bash(pytest *)`, `Bash(lake *)`, `Bash(mvn *)`). Nothing else: no network tool, no package installation, and `git push` denied.
   - Launch it in the background, from the worktree, and record its process id and `--session-id` in the register:

     ```text
     claude -p --session-id <uuid> --model <id> --setting-sources "" --strict-mcp-config
       --tools "Read,Grep,Glob,Edit,Write,Bash,Agent"
       --disallowedTools Skill "Bash(git push *)"
       --agents "<scratch>/agents.json" --append-system-prompt-file "<scratch>/protocol.md"
       --permission-mode dontAsk --allowedTools Edit Write "Bash(git *)" <one rule per oracle>
       "Audit <document> <options>. Register: spec-audit/<slug>/register.md."
     ```

     `--setting-sources ""` loads no settings file, hence no plugin, no hook and no connector of yours, and no default model either, which is why `--model` is always given (the skill's `--model`, otherwise your session's model); `--strict-mcp-config` admits no MCP server; `--tools` names the built-in tools, `--disallowedTools Skill` removes the skills, and `dontAsk` denies anything that would prompt, so the allow list is the whole of what the session may run. The CLI's `--bare` mode is not used: it only accepts an API key and refuses the usual sign-in. The built-in agents (general-purpose, Explore, Plan) stay visible to that session; the protocol tells it to launch the two of `agents.json` only.
   - Wait for the process to end. It writes the report (`spec-audit/<slug>/report.md`) and leaves the register in the state it reached; you then run phase 8 from both. In that session, every question of this skill follows its non-interactive rule: a critical fix stays pending (unless `--auto`), an undecided error is escalated in the report, and closing is not run.
   - With `--in-session`, continue here: you are the orchestrator, and the oracle table binds you the same way.
7. **Inventory.** Build `spec-audit/<slug>/inventory.md`: every definition, lemma, proposition, theorem and algorithm, with its statement and the results it uses. This dependency graph is used to establish causal links (phase 3), to propagate fixes (4.4) and to look for errors of the same class (4.2).
8. **Baseline.** Run the whole corpus, from the worktree alone, with the commands of the oracle table. It must be green; a guard that is already red becomes an iteration-0 error, never a test to be touched up.
9. **Mechanical lint.** Write once in the corpus a deterministic script that checks: continuity and uniqueness of numbering, existence of the target of each cross-reference, presence of each cited key in the bibliography and citation of each entry, balance of math delimiters, symbols used before their definition when detectable. It feeds the editorial track.

## Phase 1 — Complete cold detection

All errors of the iteration are detected before any is confirmed, tested or fixed: causal sorting (phase 3) only makes sense on the full set of errors.

Each reviewer is fresh and receives a fixed message that says nothing about the audit:

```
Review this document in full, as a referee discovering it: <paths>.
Normative dependencies (definitions it uses): <paths, or "none">.
Angle: <full | logic and proofs | definitions, scoping and edge cases | algorithms and complexity>.
Scratch directory for your computations: <scratch/iter-k/reviewer-x>.
Oracles of the project you may run for your tests: <oracle table of the register, or "none">.
Return your list in the format given by your instructions.
```

- Never add the register, the corpus, previous errors, fixed areas or the reason for the audit. Drawing attention to a passage already biases the review.
- The oracle table names the project's own verification artifacts (mechanized development, reference model, test runner) and their commands, which a referee would find in the repository; it says nothing about the audit. It is the only means of execution the reviewer gets beyond its own scripts.
- **First wave**: one full reviewer, plus angle reviewers if the document is long or dense. Each one reads the whole document, because an inconsistency shows between two sections, not within one.
- **Following waves**: one fresh full reviewer. If it brings new errors compared with the union of the previous waves (after deduplication, phase 2), launch one more wave. Detection is complete when a wave brings nothing new, and stops at the third wave at the latest; in that case, note "detection not saturated" in the register.
- If the document is too long for one reading, split it by sections, but give each reviewer the definition and notation sections and the list of statements from the inventory (without history), and add a pass dedicated to cross-section consistency.
- Do not modify the document during detection: all reviewers of an iteration read the same state.

## Phase 2 — Triage and deduplication

First classify each finding: error (definition above) or form defect (editorial track, phase 5). Style suggestions are discarded.

For each error, write a **fingerprint** independent of numbering and lines, which change as fixes are made: `[type] object — defect — witness`. Example: `[false statement] bound of the partial merge — ignores the case k > n — n = 2, k = 3`.

Compare it, on meaning and not on wording, with the other findings of the iteration and with the entries of the register:

- **New** → status DETECTED, phase 3.
- **Identical to a FIXED error** → **recurrence**: stop (phase 7), without fixing again.
- **Identical to a REFUTED error** → discarded. If two independent passes still raise it, the text is misleading: open an "ambiguity" form defect to clarify it without changing its meaning.
- **Identical to an UNDECIDED or ESCALATED error** → discarded, already awaiting the user.
- **Same class, other instance** → new, linked to the original error.

## Phase 3 — Cause graph

Sort the detected errors into causal chains. Since an error can have several causes and several consequences, this is a directed graph: an edge `A → B` means "A causes B".

- **There is an edge `A → B`** when B's defect comes from A: B cites or applies A, or inherits its definition, and its defect would disappear if A were correct as stated; or B's counterexample is A's, or derives from it; or the same missing scoping (hypothesis, context restriction) propagates from A to B.
- **A dependency is not a causation**: there is no edge when B's own defect would remain even if A were true. B is then a root for that defect. But B still uses A, and its use of A is not covered by its own fix: if A is confirmed, B also becomes a suspect behind A (4.1). B can thus be both a root for its own error and a suspect behind A.
- Rely on the inventory and on the probable causes reported by the reviewers. Justify each edge in one sentence in the register.
- **Doubtful link**: no edge, B is treated as a root, but the processing order follows the inventory's dependencies, so B comes after its presumed cause anyway.
- **Roots**: errors with no open cause.

**Causal loop.** If the graph contains a cycle (A causes B which causes A, directly or not), stop the verification: no more fixes, immediate report to the user with the errors of the cycle and the justification of each edge. There is no bottom to start from: either the document reasons in a circle, or the causal analysis is wrong, and in both cases the decision belongs to a human. Redo this check every time the graph changes (4.1, 4.4, 4.5).

## Phase 4 — Bottom-up fixing

```
while an open error remains in the graph:
    current roots = open errors all of whose causes are
                    FIXED, REFUTED or RESOLVED
    for each root, in the inventory's dependency order:
        4.1 confirmation (+ suspects) → 4.2 guards (red) → 4.3 fix (green) → 4.4 propagation
    for each consequence all of whose causes are handled, suspects included:
        4.5 reassessment
    cycle check (phase 3)
```

As long as its cause is not fixed, a consequence is **ignored**: status BLOCKED (by F-…), neither adjudicated, nor tested, nor fixed. Its analysis would bear on a text that is about to change, and its fix would risk compensating for the cause instead of repairing it.

### 4.1 Confirmation

The root goes to a fresh adjudicator, with the error alone (without the reviewer's identity or the other errors), the document paths, the oracle table of the register (phase 0, step 4) and a scratch directory. Do not adjudicate yourself, especially an error that touches a passage you fixed: you would be judging your own work.

- **CONFIRMED** (with executed evidence) → mark its suspects (below), then 4.2.
- **REFUTED** (with the reason) → remove its outgoing edges; its consequences with no other open cause become roots.
- **UNDECIDED** (with what would settle it) → escalated to the user, no change; its consequences, suspects included, remain BLOCKED and appear in the report. Its uses are not marked as suspects: nothing in the text changes, so there is nothing to reassess; the final report lists them as conditional results.

A user decision on an escalated error counts as the adjudicator's verdict: judged false, the error becomes CONFIRMED and its suspects are marked at that point; judged correct, it becomes REFUTED.

An error of type "false statement" requires an **executed** counterexample; otherwise it is downgraded to incomplete proof or UNDECIDED.

**Evidence.** The adjudicator confirms with the strongest oracle of the table that covers the statement, and says which:

1. **formal**: the statement has a counterpart in a mechanized development of the project (the document's correspondence table says which theorem or definition). The counterexample is executed on that formal statement: by evaluation or decision (`#eval`, `decide`, an exhaustive enumeration on a bounded instance type), by a property-based search (Plausible or its equivalent), or as a theorem refuting the statement on a witness. A script that re-encodes the statement confirms nothing at this level: the encoding, not the text, would be judged.
2. **model**: a reference model or checker of the project covers the statement; the counterexample runs on it.
3. **ad hoc**: no oracle covers the statement; the adjudicator's own script, in exact arithmetic, as before.

The level is recorded in the register (`Evidence`). A statement of level 1 confirmed at level 3 stays UNDECIDED, with "a formal counterexample" as what would settle it; a statement of level 2 confirmed at level 3 is CONFIRMED but flagged. The final report counts confirmations by level.

If the adjudicator names an **upstream cause**, the root was not one: if that cause is already an error in the graph, add the edge; otherwise open a new error for it, in phase 3. The root goes back to BLOCKED behind its cause, and the cycle check is redone.

**Suspects.** A result C that uses A is correct if A is granted, so no reviewer flags it. Once A is confirmed false, nobody knows whether C holds until A is fixed, and a conditional result must never leave the audit presented as safe. So, as soon as A is CONFIRMED and before 4.2, every result or passage that uses A directly becomes a **suspect**, even if it is correct granting A. The list is the union of the uses of A recorded in the inventory and of the adjudicator's `impact` field. Each suspect that is not already a consequence of A in the graph is added to it, with the origin `suspect (uses F-…)` in the register:

- as a consequence of A, with the edge `A → C` justified by "uses F-…, confirmed false as stated";
- with the status BLOCKED (by F-…).

A result already in the graph for its own defect, without an edge from A (phase 3), still gets this suspect entry: it is a root for its own error and a suspect behind A, and the two are settled separately.

The same rule applies when a consequence is CONFIRMED in 4.5: its own uses become suspects in turn. Propagation is thus transitive, but only along confirmed links: the uses of a suspect that turns out to hold are never marked. Redo the cycle check after these additions.

A suspect is settled only once its cause is fixed (4.5). If the cause stays unfixed (UNDECIDED, critical fix refused or pending, fix reverted after a regression), its suspects stay BLOCKED until the end of the audit, and the report lists them as results conditional on an unresolved error.

### 4.2 Documentation and guards, before the fix

Write the guard before the fix: written afterwards, it tends to test the fix rather than the error.

1. **Register**: a complete entry (format in `references/register.md`), including the probable cause. The cause (implicit hypothesis, forgotten edge case, neighboring result copied over…) tells where to look for sibling errors.
2. **Guards**, in the corpus:
   - **Witness guard**: encodes the original statement and checks that it fails on the counterexample (it documents the error), then that the fixed statement holds on it.
   - **Variants**: at least two more cases among the relevant edge cases (empty, singleton, 0 and 1, equalities and ties, duplicates, extreme values, missing value or NULL, non-total order, overflow), and a **near-case** where the original statement is true, which protects against over-correction.
   - **Bounded check** of the fixed statement: exhaustive on a small domain, or property-based with a fixed seed.
   - **Class guard**: search the inventory for the statements exposed to the same pattern (same forgotten hypothesis, same edge case, same quantifier) and add a guard for each, even if they are correct today. A sibling statement that turns out to be false becomes a new error, added to the graph.
   - **Incomplete proof**: a guard on the intermediate claim of the faulty step, tested on bounded instances under the hypotheses available at that point.
3. **Red first**: run the guard against the original wording; the assertion on the original statement must fail, proof that the guard detects the error. Record the result in the register.

Corpus rules:
- it only grows: never delete or loosen a guard to make it pass; any change to an existing guard is justified in the register and flagged in the report;
- exact arithmetic (integers, rationals, symbolic computation), never equality between floats; fixed seeds;
- the model encoded in the guard follows the document's definitions, not the proposed fix;
- follow the conventions of the existing corpus (headers, naming, test runner);
- a guard is written for the oracle that confirmed the error, at its level: for a formal oracle, a theorem or a decided check in a module that the project's build compiles, so that replaying the corpus is the build (Lean example in `references/register.md`); for a model, a test that runs the model; otherwise a test of the runner. "Red first" then means that the theorem refuting the original statement on the witness compiles, and "green" that the fixed statement is re-proved, or passes its bounded check, in the same build. A decision procedure that extends the trusted base (`native_decide`) serves the search, never the recorded guard.

### 4.3 Fix

Choose the nature of the fix, and record it:

- **statement fix**: the conclusion is weakened or corrected;
- **scoping addition**: a hypothesis is added, or the context or domain of application is restricted, so that the statement becomes true again;
- **proof completion or repair**: the statement holds, the faulty step is justified or replaced.

They can be combined if needed. In all cases:

- **Minimal fix**: the weakest change that makes the statement true and keeps its uses valid. Never strengthen a statement, do not introduce a new result to plug a gap, never delete a result silently: a withdrawn result is marked as such, with the reason and the counterexample.
- **Critical fixes**: changing the statement of a main result (theorem, result cited in the abstract) or withdrawing a result changes what the document claims. By default, first handle the non-critical roots, then present the pending critical fixes to the user together (statement before and after, counterexample, impact) and wait for their approval; their chains, suspects included, remain BLOCKED until then, and stay BLOCKED if the user refuses. With `--auto`, apply them and flag it in the report.
- **Green**: run the error's guard, then the whole corpus. A green guard that turns red is a regression: revert the fix and set the error back to UNDECIDED; its consequences and suspects stay BLOCKED.
- **Internal revision**: once the error is FIXED, commit in the worktree the document, its guards and the register as internal revision r<N> (numbered from 1 over the whole audit), with a message that marks it incomplete: `spec-audit(<slug>): r<N> — F-… fixed [incomplete: audit in progress]`. Record it in the register. Each revision is a verified state, every guard green, to which a stop or an interruption can return without losing the fixes already made. It is incomplete because the consequences of the error may not have been reassessed yet. The mark stays in the commit message and the register, never in the document: the reviewers read the document and must not learn that an audit is running.
- **Traceability**: if the document has an errata, history or revision section, or if the project versions its documents, record the fix according to that convention.
- **Mapped statements**: when the fixed statement has a counterpart in a mechanized development (evidence level 1), the fix includes the change of the formal statement and of its proof, and the update of the correspondence table, in the same internal revision. Without them the error stays at "incomplete proof", never FIXED: the text would claim what the development no longer proves.

### 4.4 Propagation

Starting from the inventory, recheck everything that depends on the fixed statement: later results, proofs that cite it, examples, tables, abstract, introduction, conclusion, other project documents, code or mechanization that refer to it. This covers every use, including those without an edge in phase 3: a result with its own defect still uses the statement, and the fix can break it in another way. What a use must still get from the fixed statement depends on the nature of the fix:

- **statement fix**: the conclusion has changed, so every use that relied on the original conclusion becomes a new error, unless the fixed conclusion still gives it what it needs;
- **scoping addition**: every use must satisfy the new hypothesis; a use that no longer satisfies it becomes a new error;
- **proof completion or repair**: the statement is unchanged, so its uses are not affected.

A new error is a consequence of the root (edge root → new error), handled in the same loop. Uses already in the graph as suspects are not duplicated: their reassessment (4.5) settles them. Propagation catches the uses that the inventory and the adjudicator missed when the suspects were marked.

### 4.5 Reassessment of consequences

When all the causes of a consequence are handled, send it to a fresh adjudicator, who judges it against the fixed text. Suspects are reassessed the same way. To limit the cost, a single fresh adjudicator can reassess all the suspects of the same cause, with one verdict per suspect: they all read the same fixed passage.

- **REFUTED** → status RESOLVED (by F-…); for a suspect, this means that the result holds against the fixed text. Add its case to the cause's guards: if the cause regressed, the consequence would show it too.
- **CONFIRMED** → it becomes a root and follows the full protocol (4.2 to 4.4); its own uses become suspects in turn (4.1).
- **Change of nature** → new error, added to the graph.

**Proof repaired, statement unchanged.** If the cause was an incomplete proof repaired without any change to its statement, its suspects go straight to RESOLVED (by F-…), without adjudication: they were only conditional on the repair, and nothing they use has changed.

## Phase 5 — Editorial track

After the iteration's substantive fixes, which can move the text and the numbers:

- rerun the lint and fix what it reports;
- fix typos outside formulas (spelling, grammar, layout); any change to a formula, symbol, index, quantifier or inequality is an error, not a form defect;
- **numbering**: prefer stability (insertion as 4.3′ or 4.3a). If renumbering is unavoidable, update all cross-references, internal and external, and record the old → new mapping;
- **bibliography**: only fix a reference against its source (local PDF, publisher's page, DBLP…); otherwise mark it "to be checked" and leave it as is. Never invent metadata: pages, DOI, theorem number;
- for each class of defect fixed, add a rule to the lint, so that it is detected mechanically from now on.

## Phase 6 — End of iteration

Run the whole corpus and the lint: everything must be green. Commit locally in the worktree (message listing the identifiers of the errors and defects handled), only your files, without pushing; this commit is also an internal revision (4.3). Update the register's log.

## Phase 7 — Loop and stop

Go back to phase 1 with new agents. Stop at the first condition met:

1. **Convergence**: a complete cold detection produces no confirmed error. If the previous iteration changed the statement or the scoping of a result, require a second clean detection: that is where new errors are born.
2. **Causal loop**: the cause graph contains a cycle (phase 3).
3. **Recurrence**: an error is identical to an already FIXED error. Stop without fixing again: either the fix did not hold, or two fixes contradict each other. Report both entries and the diff at fault.
4. **Oscillation**: a proposed fix would undo, even partially, an earlier fix of the audit; or the same fix has produced two successive confirmed errors.
5. **Non-convergence**: the number of confirmed errors does not decrease over two consecutive iterations. The document probably needs human rework rather than patches.
6. **Budget**: `--max-iter` reached.
7. **Exhaustion**: detection only finds form defects. Finish the editorial track, rerun the lint and the corpus, then stop.

Never conclude "the document is correct". Conclude "N independent detections found no further confirmed error", stating what was not checked.

## Final report

Write it in `spec-audit/<slug>/report.md`, in the worktree; the summary to the user comes with closing (phase 8):

```markdown
# Precision audit — <document>

## Result
Stop reason, iterations, errors confirmed / refuted / resolved by their cause / undecided / blocked, suspects added / cleared / confirmed (counted apart from the errors), form defects fixed, commits.

## Cause graph
Per iteration: roots, chains, and for each edge its justification. Any cycle first.

## Modified statements
For each result touched: before → after, nature (statement fix, scoping, proof), counterexample, guards.

## Errors
| ID | Severity | Type | Causes | Status | Fix | Guards | Commit |

## Open points
Undecided errors and the chains they block, references to check, recurrences, oscillations, modified guards, pending critical fixes, detection not saturated.
Results conditional on an unresolved error, directly or through another result: for each, the error it depends on and the chain through which it uses it.

## Corpus
Guards added, lint rules added, command to replay everything.

## Scope of verification
What was checked and how (agent review, bounded exhaustive test, mechanized proof), the confirmations by evidence level (formal, model, ad hoc), the oracles used and the session resources ignored, and what was not checked.
```

**Conditional results.** Before writing "Open points", take each unresolved error: UNDECIDED or ESCALATED, CONFIRMED with a critical fix refused or pending, or with a fix reverted after a regression. From the inventory, collect every result that depends on it, directly or through another result, and list them grouped by direct use, each with what it uses. Suspects only cover the direct uses of a confirmed error; this closure also reaches the uses of an undecided error and the results that depend on a suspect. It changes nothing in the graph: the text has not changed, so there is nothing to reassess, only results that must not be presented as safe.

End the report with the branch and the worktree (path, branch `audit/<slug>`, base, commits) and with the audit outcome and the recommended closing option (phase 8).

Review by agents and bounded tests are neither peer review nor proof. Never write that a proof is "verified" without saying by what; only a mechanized proof can be called machine-verified.

## Phase 8 — Closing

Closing is decided with the user, through a multiple-choice question, after they have been able to read the report. It is run by the launcher (your session) from the report and the register written by the audit session, or by you with `--in-session`.

### 8.1 Classify the outcome

| Outcome | Condition |
|---|---|
| **Success** | stop by convergence or exhaustion; corpus and lint green; no UNDECIDED error, no BLOCKED chain or suspect, no pending critical fix |
| **Partial, to continue** | stop on budget, or detection not saturated; corpus and lint green |
| **Partial, needs decision** | points awaiting a human decision: UNDECIDED error, BLOCKED chain, result conditional on an unresolved error (BLOCKED suspect), critical fix refused or pending; corpus and lint green |
| **Failure** | causal loop, recurrence, oscillation, non-convergence, corpus or lint red, or stop on an execution error |

### 8.2 Present the report

Summarize the audit in the session (outcome, stop reason, errors confirmed and fixed, modified statements, open points) and give the path of the full report, `<worktree>/spec-audit/<slug>/report.md`, to be read before choosing.

### 8.3 Ask the question

Use the multiple-choice question tool (AskUserQuestion): a single question, with the header "Closing", that recalls the outcome and the report path. The options:

| Option | Effect |
|---|---|
| **Accept and merge** | merge of `audit/<slug>` into the original branch after the safety checks (8.5), then removal of the worktree and the branch |
| **Run another check** | new series of iterations in the same worktree (8.7), without merging anything |
| **Keep the worktree** | neither merge nor removal; report and patch archived in the original branch; decision postponed |
| **Abandon** | report, register and patch archived in the original branch, then removal of the worktree and the branch (8.6) |

The tool always adds a free answer ("Other").

Put the recommended option first, with "(Recommended)" at the end of its label. It is the safest option for the outcome:

| Outcome | Recommended | Also offered | Why |
|---|---|---|---|
| Success | Accept and merge | Run another check, Keep, Abandon | every fix is confirmed and guarded, the corpus is green |
| Partial, to continue | Run another check | Accept, Keep, Abandon | a new series can close the remaining points without touching the original branch |
| Partial, needs decision | Keep the worktree | Accept, Run another check, Abandon | a new pass will not settle what awaits a human decision, and keeping loses nothing |
| Failure | Abandon | Keep; Accept only if corpus and lint are green | the automatic process can no longer make progress, and the archive keeps everything |

Rules:

- Never offer "Accept" if the corpus or the lint is red.
- Do not offer "Run another check" after a causal loop, a recurrence, an oscillation or a non-convergence: a new pass would go round in circles. After a "Run another check" that fixed no new error, recommend "Keep" rather than "Run another check".
- Interpret a free answer; if it is ambiguous, ask again. Never merge or delete on an ambiguous answer.
- If the question cannot be asked (non-interactive session), or with `--keep`, apply "Keep the worktree": it is the only option that changes nothing and loses nothing.
- Record in the register the question, the recommended option and the answer, and its new state: `closed` after "Accept" or "Abandon", `suspended` after "Keep the worktree", still `running` after "Run another check".

### 8.4 Bring the report back

In every case, before any removal:

- **In the session**: the summary from 8.2, completed with the closing performed (merge commit, archive, worktree kept or removed).
- **In the original branch**:
  - *Accept*: the report, the register, the inventory and the guards arrive with the merge.
  - *Keep* or *Abandon*: first commit in the worktree any work in progress, with a message marking it as unverified. Then copy into the original repository, under `spec-audit/<slug>/<YYYY-MM-DD>-<outcome>/`, the `report.md`, the `register.md` and a `corrections.patch` produced by `git -C "<worktree>" diff <base> audit/<slug>`. This patch contains the fixes and the guards: nothing is lost, even after abandoning. Commit only these files (`git add -- <paths>` then `git commit -m "<message>" -- <paths>`), so as not to carry along any change from another session. If the project rules forbid this commit, leave the files uncommitted and say so.
  - *Run another check*: nothing for now; the report of the next series will go through this same closing.

Never abandon a worktree before this return has succeeded.

### 8.5 Merge ("Accept and merge")

1. Check that the original repository is still on the branch recorded in phase 0. Otherwise, do not merge: keep the worktree and ask the question again.
2. If the original branch has moved since the base, integrate it into the worktree: `git -C "<worktree>" merge <original branch>`. On conflict, `git merge --abort`, keep the worktree and report that the merge is blocked; the audit itself has not failed.
3. Rerun the whole corpus and the lint in the worktree: everything must be green, otherwise keep the worktree and report.
4. Merge into the original repository: `git -C "<original repository>" merge --no-ff audit/<slug> -m "<message following the project's conventions>"`. Since the audit branch already contains the original head, no conflict is possible any more; if git refuses because of uncommitted changes in the original repository, do not force and do not stash: keep the worktree and report.
5. Remove the worktree (`git worktree remove "<worktree>"`), then the branch (`git branch -d audit/<slug>`, which refuses to delete an unmerged branch).
6. Never push.

### 8.6 Abandon ("Abandon")

After the return: `git worktree remove --force "<worktree>"`, then `git branch -D audit/<slug>`. The archived patch makes it possible to replay all or part of the fixes, or to examine them.

### 8.7 New check ("Run another check")

Resume at phase 1 in the same worktree, with new agents and a new budget equal to `--max-iter`. The register continues (identifiers are never reassigned), the guards stay in place, and the series ends again with this phase 8.

### 8.8 Interruption

If the session is interrupted before closing (error, session closed), the worktree and the branch stay in place, and the last internal revision is the latest verified state: `--resume` resumes the audit from it (phase 0, step 5), or phase 8 can be replayed on its own.

### 8.9 Stop on request

The user can stop the audit at any time, from this session only: by pressing Esc then running `/spec-audit:stop`, or by asking in words. Esc alone interrupts your turn, not the background agents.

In the default mode, the audit runs in its own session (phase 0, step 6), launched by you: stop that process first (its id is in the register; `taskkill /PID <pid> /T` on Windows, `kill <pid>` elsewhere), which ends its agents with it; then continue at step 2, taking stock from the register and the worktree's git state. With `--in-session`, start at step 1:

1. **Stop the agents.** Launch nothing new. Stop every audit agent still running with `TaskStop`, using the name given at launch; if that tool is not available, ask the user to stop them (`/tasks`, or the tasks pane of the desktop app). Ignore any result that arrives afterwards. The agents write only to their scratch directories, so a late one cannot damage the document: stopping them saves cost and keeps the stop clean.
2. **Take stock.** Set the register's state to `stopping`, and record the step in progress and the uncommitted changes since the last internal revision: they are unverified.
3. **Report** in the session: the last internal revision (commit, errors fixed up to it), marked incomplete, with what it lacks (consequences not yet reassessed, errors not yet handled, detection not finished), the step in progress, and the path of the register.
4. **Ask**, with AskUserQuestion: a single question with the header "Stop". It is the user, not the audit, who decides whether the last revision becomes the new base:

| Option | Effect |
|---|---|
| **Suspend** | nothing is merged or deleted; state `suspended`; `--resume` continues from the last revision |
| **Keep the last revision as the new base** | save the uncommitted changes to the document and the corpus as `spec-audit/<slug>/in-flight-<YYYY-MM-DD>.patch` and restore them to the last revision; write the report, marked "Incomplete audit — stopped at r<N>"; commit the register, the report and the patch; then merge as in 8.5, with a merge message marking the audit incomplete. A later audit starts from this base |
| **Cancel** | write the report, marked "Incomplete audit — cancelled"; archive as for "Abandon" (8.4), then remove the worktree and the branch (8.6) |

- Put "Suspend" first, with "(Recommended)": it changes nothing and loses nothing.
- Offer "Keep the last revision" only if a revision exists, that is, once at least one error has been fixed.
- If the merge does not go through (8.5), keep the worktree: the audit stays suspended.
- Interpret a free answer; if it is ambiguous, ask again. Never merge or delete on an ambiguous answer. If the question cannot be asked, suspend.
- Record the question and the answer in the register, and set its state to `suspended` or `closed`.
