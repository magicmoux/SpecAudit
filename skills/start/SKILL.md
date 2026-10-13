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
argument-hint: "<document> [--corpus <dir>] [--max-passes N] [--auto] [--resume] [--base <ref>] [--no-worktree] [--in-session] [--model <family|id>] [--model-version <v>] [--keep] [--no-discharge] [--fail-fast] [--account <email>] [--pause-at <N|session=N,week=N|off>] [--no-auto-resume]"
---

# Precision audit of a specification

An author cannot see their own blind spots, and a reviewer who knows the history reads what they expect to read. This skill therefore separates the roles: fresh reviewers who know nothing of the audit, an adjudicator who confirms or refutes each error, and you, the orchestrator, who keep the register, sort the errors, write the guards and make the fixes. Three principles:

- **An unconfirmed error is not an error.** Reviewers produce false positives, and fixing a correct statement damages the document as much as leaving a false one.
- **Fix a cause before its consequences.** Fixing a consequence first masks the cause, or compensates for it locally (a hypothesis added in the wrong place).
- **An error fixed without a guard will come back.** Every fix leaves a test in the corpus that would fail if the error reappeared.

## What counts as an error

An **error** is a content defect specific to the document's domain, as the profile's `Errors` section defines it. Only errors follow the full protocol: cause graph, counterexample, guards, bottom-up fixing.

**Form defects** (the profile's `Form defects` section) are not errors in the sense of this protocol: they follow the editorial track (phase 5), without counterexample or causal chain. Style preferences are discarded (phase 2).

## Profile

What counts as an error, as evidence and as a guard depends on the kind of document; the rest of this protocol does not. A profile in `profiles/` holds the domain-specific part, in sections named here: `Errors`, `Form defects`, `Inventory units`, `Reviewer angles`, `Oracles`, `Evidence`, `Guards`, `Fixes`, `Lint`. The only profile so far is `formal` (`profiles/formal.md`: theory, proofs, algorithms, formal specifications); the project's architecture gives the profile of each audited document ("Project architecture"); read it at phase 0 and apply it wherever one of its sections is named. The other profiles are designed in the plugin's `docs/profiles.md`.

**Where the plugin's files are.** This skill's folder is `${CLAUDE_SKILL_DIR}`; `profiles/…` and `references/…` are relative to it, and the plugin's `agents/` and `docs/` folders are in `${CLAUDE_SKILL_DIR}/../../`. Read them from there, never from the working directory or an inferred plugin root: the skill folder is the one location the harness guarantees, and a guessed path that does not exist, or that the permission mode refuses, stops the audit at phase 0 before anything is recorded. Profile: `${CLAUDE_SKILL_DIR}/profiles/formal.md`; register format: `${CLAUDE_SKILL_DIR}/references/register.md`; launch steps: `${CLAUDE_SKILL_DIR}/references/launch.md`; closing: `${CLAUDE_SKILL_DIR}/references/closing.md`; hypothesis discharge: `${CLAUDE_SKILL_DIR}/references/discharge.md`.

## Parameters

- `<document>`: the audited file or files, or a folder standing for the documents in it: list them at phase 0 (files of the document's formats, recursively, minus what the project ignores) and record the list in the register, so that the audit, its report and its index entry say exactly what was audited. Each must have the role `audited` in the project's architecture ("Project architecture"); a document that has another role, or none, is not audited: say which role it has, and that `/spec-audit:init` (or an edit of `SPECAUDIT_ARCH.md`) changes it.
- `--corpus <dir>`: the global guard corpus. Default: the project's existing verification corpus if any (follow its conventions), else `spec-guards/` at the root.
- `--max-passes N`: maximum number of passes (default 5): the document is audited, fixed, then audited again as fixed, N times in all at most. A pass is what this protocol calls an iteration (phases 1 to 6). `--max-iter`, and `max-iter` in the configuration's `defaults`, are deprecated aliases.
- `--auto`: also apply critical fixes without pausing (see 4.3).
- `--resume`: resume an interrupted or suspended audit from its register, in its existing worktree, from its last internal revision (4.3).
- `--base <ref>`: starting branch or commit of the worktree (default: `HEAD` of the current repository).
- `--no-worktree`: work in the current directory, without a worktree, when it is already isolated for the audit.
- `--in-session`: run the orchestrator in the current session. By default the audit runs in its own session (phase 0, step 6), started in the worktree with the file tools, Bash, the two agents and the project's oracles, and none of your session's plugins, skills, connectors, hooks or memory.
- `--model <family|id>`: model of the audit session, inherited by its agents (`model: inherit` in `agents/`): a family alias (`opus`, `sonnet`, `fable`, `haiku`) or a full model id. Default: your session model's family, as your context names it. With `--in-session`, the agents inherit your session's model and the option is ignored.
- `--model-version <v>`: version of that family, `5.5` for instance (default `latest`). For `latest` the audit session gets `--model <family>`, since the alias names the family's latest version; otherwise `--model claude-<family>-<version with hyphens>` (`claude-opus-5-5`). Ignored when `--model` is a full id, or with `--in-session`.
- `--account <email>`: the account the audit session is billed to, as `claude auth status` names it: the launch checks it instead of asking, and stops if the CLI uses another one (`references/launch.md`, "Account"). Required to launch an audit session where no question can be asked. Ignored with `--in-session`, which runs on your session's account.
- `--pause-at <N | session=N,week=N | off>`: pause the audit once the account's usage reaches N % of its session window or of its week (default `session=75,week=50`), and resume it when the window resets (`references/launch.md`, "Usage limits"). Ignored with `--in-session`.
- `--no-auto-resume`: on a pause, stop instead of waiting for the session window to reset, saying when to resume.
- `--keep`: at closing, ask no question and apply "Keep the worktree": nothing is merged or removed, and the results folder and the index entry come back to the original branch as for any closing that keeps (phase 8).
- `--fail-fast`: stop at the first confirmed error, without fixing it, and report its proposed fix and the results it may affect ("Fail-fast" below). For a first look at a document, or a beta test: one detection wave instead of a full audit, enough to say whether the document needs one.
- `--no-discharge`: skip hypothesis discharge (phase 1), for a document whose use edges are too many to probe, or to compare runs with and without it.
- `--uniform-effort`: launch every agent at its usual effort, without the per-step routing ("Effort per step"): for an audit whose cost does not matter, or to compare runs step for step.

An option given on the command wins over the project configuration's `defaults`, which win over the defaults above.

## Project architecture

**No audit without `SPECAUDIT_ARCH.md`.** A project's architecture is a file at its root, `SPECAUDIT_ARCH.md`, which `/spec-audit:init` proposes and writes once the user confirms, and which the user may edit by hand. Before anything else, at phase 0 and with every option (`--resume`, `--in-session`, `--no-worktree` included), the launcher checks it: `python3 ${CLAUDE_SKILL_DIR}/references/arch.py require --root "<repository root>"` (`python` where `python3` does not print a Python 3 version; the register's interpreter is not chosen yet). The orchestrator of an audit session finds the result in the register (`Architecture`) and does not check again. If it exits 2 (no file), do not audit: say that the project has no `SPECAUDIT_ARCH.md`, that an audit follows the project's architecture rather than a guessed one, and that `/spec-audit:init` proposes it; then stop, without creating, asking or spending anything. If it exits 1 (the file does not parse, a role is unknown, nothing is audited), stop the same way with the errors it prints. Its warnings (a path not found, a profile that does not exist yet) are reported and recorded in the register.

The architecture gives each path one role, and the audit follows it for the whole audit:

| Role | The audit |
|---|---|
| `audited` | checks it and may fix it, with the profile the file gives |
| `original`, `prior-version` | never changes it; never gives it to an agent: an earlier version is history |
| `normative` | never changes it; gives it to the reviewers and adjudicators as a normative dependency (the file's `Normative dependencies` table says which document uses which; without a row, every `normative` path) |
| `sources` | never changes it; checks the bibliography against it (phase 5) |
| `oracle` | never changes it, except where its `Guards` cell says new guard modules go, and except the counterpart and correspondence table of a mapped pair, together with its document (below); runs it with the command its row gives, which makes the oracle table (`references/launch.md`, step 4) |
| `ignored` | neither reads it nor changes it |
| not listed | never changes it; may read it |

**What the audit may change** is therefore: the `audited` paths, its guard corpus and the oracles' guard locations, its own records (`spec-audit/`, the results folder, the index), and, for a **mapped pair** (a document whose statements have a formal counterpart, the file's `Mapped pairs` table), the counterpart and its correspondence table, only in the same internal revision as the document (the profile's `Fixes`). Never `SPECAUDIT_ARCH.md` itself, nor the orchestrator's configuration. `arch.py` holds this rule mechanically, twice: in the audit session, a hook refuses at once an Edit or a Write outside it, and an agent's read of what it must not see (`references/launch.md`, step 6); and before every commit of the audit, `arch.py check --staged` refuses a change outside it ("Standing rules", Architecture).

Reviewers and adjudicators may read `SPECAUDIT_ARCH.md`: it holds only what a referee could see in the repository, the layout and the role of each part, never anything about audits. What concerns the audit (scope, focus, results not to change, notes) is in the orchestrator's configuration, below.

## Project configuration

Beside the architecture, a project keeps what concerns its audits in a configuration that only the launcher and the orchestrator read, so that every audit of the project starts from the same choices, and the choices are reviewed like the rest of the repository:

- **`.specaudit.md`** at the repository root, when the configuration is all the audit needs;
- **`.specaudit/`**, with `config.md` and the files the audit needs that the project lacks: normative references (`normative/`, glossaries, style guides, standards, listed as `normative` in the architecture to be given to the reviewers), project extensions of a profile (`profiles/<profile>.md`, extra errors or lint rules, added to the plugin's profile, never replacing it).

`config.md` and `.specaudit.md` share one format: a YAML front matter, then free notes for the orchestrator.

```markdown
---
version-convention: new revision ("<name> - revision N.md")
defaults:                      # same names as the command's options
  max-passes: 3
  corpus: mechanization/Guards
  model: opus
---

Notes for the orchestrator: scope of the theory, results not to be changed, status of the proofs.
```

It describes the audit (scope, focus, what not to touch), exactly what a cold reviewer must not know: reviewers and adjudicators never read it, nor `.specaudit/` beyond the normative files the architecture lists. If both `.specaudit.md` and `.specaudit/` exist, ask which one holds, and change nothing until the user answers. When a single file needs a companion (a normative reference the project lacks), offer to turn `.specaudit.md` into `.specaudit/config.md`.

**Deprecated keys.** The keys `profiles` (document pattern → profile) and `normative` (document pattern → normative dependencies) describe the project, not the audit: they moved to `SPECAUDIT_ARCH.md`. For this version they are still read: a profile applies to an audited document the architecture gives none, and normative dependencies are added to the architecture's (`arch.py normative --config <file> <document>` gives the union). Say once that they are deprecated and that `/spec-audit:init` moves them, and record it in the register and in the report's scope of verification. Where they contradict the architecture, the architecture holds.

## Roles

| Role | Who | Sees | Writes |
|---|---|---|---|
| Launcher | you | your session, the original repository, the register | worktree and register (phase 0, steps 1 to 6), stop (8.9), closing (phase 8) |
| Orchestrator | the audit session (phase 0, step 6), or you with `--in-session` | everything in the worktree: register, corpus, oracles, git history | document, corpus, register |
| Reviewer | `spec-reviewer` agent, fresh for each wave | the document, its normative dependencies and `SPECAUDIT_ARCH.md`, nothing else | nothing, outside its scratch directory |
| Adjudicator | `spec-adjudicator` agent, fresh for each error, guard or probe | one error, one guard or one use edge, the document and `SPECAUDIT_ARCH.md` | nothing, outside its scratch directory |

**Isolation line.** Every message you write to a reviewer or an adjudicator, whatever its step (detection, confirmation, reassessment, guard review, probe; not the preflight), ends with this line, word for word: "You may read SPECAUDIT_ARCH.md, the project's layout. Never read SPECAUDITS.md, the SpecAudit-*/ folders, spec-audit/ (outside your scratch directory), .specaudit.md or .specaudit/ (beyond the normative dependencies above), nor the paths SPECAUDIT_ARCH.md marks original, prior-version or ignored." It names no audit, error or passage: it repeats the agent's own rules, so that a message alone keeps it from the history.

Installed in `~/.claude/agents/`, these agents are called `spec-reviewer` and `spec-adjudicator`; as a plugin, `spec-audit:spec-reviewer` and `spec-audit:spec-adjudicator`. If they are unavailable, launch a fresh general-purpose agent with the content of `spec-reviewer.md` or `spec-adjudicator.md` as instructions (from `~/.claude/agents/`, or the plugin's `agents/` folder). Never use a "fork" agent: it would inherit the conversation, hence the history. Name each agent at launch `audit-<slug>-<role>-<id>` (for example `audit-selection-adjudicator-F-1-3`) and pass the name as its `description`: the Agent tool has no name parameter, and the description is what `/tasks`, the tasks pane and the task notifications show, so it is how a person recognizes the agent. At launch, record it in the register's agent table (name, the agent id the launch returns for a background agent, role, error or wave, scratch directory, state `running`), and set its state to `done` when its result arrives: `TaskStop` takes that id, not the name (8.9), and after a stop or a crash, that table is the only list of what was in flight.

In the audit session, the agents are passed at launch (`--agents`, phase 0, step 6) from the plugin's `agents/` folder, under the same names.

**Agent journal.** In the audit session, hooks keep each agent's journal in its scratch directory, without you or the agent writing anything (`references/journal.py`): `prompt.md`, its message word for word, at launch; `journal.jsonl`, one line per tool call, with its input and the start of its output; `result.md`, its final reply, when it ends. An agent launched in a scratch directory that holds a prompt and no result is a replacement: the hook sends it the original prompt, word for word, and keeps the message you wrote beside it (`prompt.rewritten.md`). An agent stopped, killed or cut by a usage limit keeps its prompt and its journal up to its last tool call, and has no `result.md`; one that ended on a stop request (closing, 8.9) leaves its state in `partial.md` instead. If a launch or a tool call is refused with `stop requested`, launch nothing more, wait for the agents running, record their state, commit, set the state to `suspended (stopped on request)` and end. The same hooks hold the usage threshold (`--pause-at`): past it, a launch is refused, the Agent tool's error starting with `paused: usage limit`. Then launch nothing more: record the refused agent `pending` in the agent table (its `prompt.md` is kept), wait for the agents already running ("Questions only when idle"), record their results, set the register's state to `suspended (usage limit: <window>, resumes <resumeAtLocal>)` with the content of the request, and stop; the launcher resumes the audit when the window resets. A `--resume` then relaunches only the agents with a prompt and no result, with that prompt, and reads the others' `result.md` instead of launching them again. With `--in-session` there are no such hooks: an interrupted agent is replaced with the message the register's agent table describes.

**Replacing an agent.** Claude Code cannot pause an agent, so the audit is made safe to interrupt by making every agent replaceable. Never resume a stopped or lost agent with `SendMessage`: Claude Code refuses messages to an agent the user stopped, and some tools deny `SendMessage` altogether (tokenforge's lean mode). Launch a fresh agent under a new name, with the same message and scratch directory, and set the old one to `replaced by <name>`. The scratch directory keeps the stopped agent's journal, scripts and outputs, so the replacement redoes only its judgment, on the text as it is now, not its computations.

## Context economy

A fresh review at every fix makes the audit trustworthy, and long: every agent starts from nothing, and you carry the audit between them. Spend context on checking, not on remembering:

- **Each agent gets what its step needs, and nothing more**: a reviewer the document and its normative dependencies, an adjudicator one error or consequence with its passage (4.5, "Handover"), a guard review one guard with its passage. What an agent was not told cannot bias it, nor fill its context.
- **You work from the chain digest**, not the whole register: once an error is FIXED or RESOLVED, write its one-line digest in the register (format in `references/register.md`): statement before and after, guards, open suspects. That line is what the rest of the chain needs; reread the full entry only when an agent's result concerns that error. After a compaction or at `--resume`, reread the header, the digest and the open entries, not every entry.
- **The protocol is loaded in parts**: phase 0's launch steps and phase 8's closing are in `references/`, read when they come; the audit session never loads them.

## Effort per step

Every agent of a step does the same kind of work, so you set its effort when you launch it, from what the step is, rather than leaving every launch at the same level. The steps differ: a cold review of the whole document, or the confirmation of a critical error, is where the quality of the audit is decided; reassessing the suspects of one cause against one fixed passage, or reviewing one guard, is a narrow question on a short text. This protocol explicitly asks you to set the Agent tool's `effort` as follows, unless `--uniform-effort` is given:

| Step | Effort | Why |
|---|---|---|
| Reviewer (phase 1), every wave and angle | usual (omit `effort`) | what detection misses, nothing downstream recovers |
| Adjudicator of an error (4.1), critical or major, or whose statement has a formal or model oracle | usual | a wrong verdict damages a correct statement or leaves a false one |
| Adjudicator of a minor error, at the ad hoc level | `medium` | a short statement, checked by a script that runs whatever the effort |
| Probe of a use edge (phase 1, hypothesis discharge) | `medium` | one hypothesis on one use, decided by a search that runs whatever the effort |
| Reassessment of consequences and suspects (4.5) | `low` | one question per result, against one passage as it reads now ("Handover") |
| Guard review (corpus errors) | `low` | one guard and one passage |

All agents keep the audit session's model (`model: inherit`): a cheaper model is not something the evals have validated, and one model keeps the verdicts comparable.

**Escalation.** A lowered effort is a bet that the step is easy; take it back as soon as the result shows otherwise, from what you can observe rather than from the agent's own estimate of its difficulty, since an agent that misreads a definition rarely knows it. Relaunch a fresh agent at the usual effort, on the same message and scratch directory (it reuses the scripts and outputs there), once, when:
- the verdict is UNDECIDED, or the agent reports that it could not execute;
- the evidence level reached is weaker than the statement allows (a statement with a formal counterpart confirmed only ad hoc);
- a guard review or a reassessment contradicts what the earlier steps established (a guard FAULTY on a fix the corpus otherwise accepts, a suspect CONFIRMED where its cause's fix was a mere rewording);
- the agent sets `escalate` in its verdict: an extra signal, which can add an escalation, never avoid one.
Record the effort of each launch, and each escalation with its trigger, in the agent table: the report says which steps ran at which effort.

## Questions only when idle

Ask the user a question (AskUserQuestion) only when no audit agent is running: first wait for the completion notifications of the agents already launched, launching none meanwhile. A question blocks you, not the background agents: they keep running and spending while the user reads, and their results then land on a state the answer may change (a critical fix refused, an error judged correct). Since an agent cannot be paused, waiting is the only way to have nothing in flight when the user decides. The one exception is the stop on request (8.9), which stops the agents instead: the user asked for the spending to end.

**When no question can be asked.** If AskUserQuestion is unavailable (a non-interactive session: the audit session, `claude -p`, an eval, a routine), never ask in plain text and end your turn to wait for the answer: there, ending the turn ends the audit, leaving neither report nor results folder, and nobody is there to answer. Apply instead each question's non-interactive rule, record in the register that it applied, and go on to the end: a critical fix stays pending (unless `--auto`), an undecided or escalated error stays open in the report, a corpus error the adjudicator could not settle stays BLOCKED, and closing applies "Keep the worktree" (8.3).

## Phase 0 — Preparation (once)

**Standing rules, from the first step to the last.** Phase 0 is done once, but these rules hold for the whole audit, in every session that runs it, the audit session included:
- **Architecture.** Change only what `SPECAUDIT_ARCH.md` lets the audit change ("Project architecture"). Before every commit of the worktree, once its paths are staged, run `arch.py check --staged --root <worktree> --corpus <corpus>` in the form the table below gives. If it refuses a path, the change was a mistake of the audit, not a fix: unstage and restore that path (`git restore --staged --worktree -- <path>`, or `git rm --cached -- <path>` and Write nothing back for a new file), commit the rest only if it still stands alone, and record the attempt in the register as an error of the audit (`Architecture refusals`: path, role, the step and the error whose fix touched it). In the audit session, the hook refuses the Edit or the Write itself; record that refusal the same way. A fix that needs a path the audit may not change (a normative document, a source, the original, an oracle outside a mapped pair) is not made: the error stays CONFIRMED, its fix proposed in the report as for a pending critical fix, and its consequences and suspects stay BLOCKED.
- **Project rules.** `CLAUDE.md`, the project's conventions and its memory take precedence over this skill (attribution headers, document versioning, commit messages, push policy, scope of the theory, status of proofs): read the worktree's `CLAUDE.md` when you start, since an audit session does not load it on its own. The project configuration's notes (`.specaudit.md`, `.specaudit/config.md`) guide you; the register records which ones apply.
- **Version convention.** Fix the document as the register's `Version convention` says: in place, or in a new revision.
- **Environment.** Use the worktree, the file tools, Bash, the two agents and the oracles of the register's table, nothing else; once the audit has started, read nothing in the original directory. In the audit session, Bash runs only what its allow list names, so every command of the audit, yours and the agents', takes one of these forms and no other; the preflight probes each of them, which is what makes it cover the whole audit:

  | To | Form |
  |---|---|
  | read, list, search, write or change a file | Read, Glob, Grep, Write, Edit (never `cat`, `ls`, redirections or heredocs) |
  | run git | `git <subcommand> …`, alone; to keep an older version of a file, run `git show <rev>:<path>` and Write its output |
  | run a script of yours or of an agent | `<python> <scratch root>/…/<file>.py`, absolute path, nothing chained |
  | run a script of the corpus (lint) | `<python> <worktree>/<corpus>/<file>.py` |
  | run an oracle or the corpus | its command exactly as the oracle table records it |
  | select or record the probes of hypothesis discharge | `<python> <scratch root>/protocol/discharge.py <select\|record> …` (with `--in-session`: `<python> ${CLAUDE_SKILL_DIR}/references/discharge.py …`) |
  | run them on another version of the document (red first) | `<python> <scratch root>/protocol/with_docs.py <path>=<file> -- <that command>` (with `--in-session`: `<python> ${CLAUDE_SKILL_DIR}/references/with_docs.py …`), which sets `SPEC_DOCS` |
  | check a commit against the architecture | `<python> <scratch root>/protocol/arch.py check --staged --root <worktree> --corpus <corpus>` (with `--in-session`: `<python> ${CLAUDE_SKILL_DIR}/references/arch.py …`) |

  `<python>` is the register's `Interpreter`, the command phase 0 found and ran (`python3`, or `python` where `python3` is missing or, on Windows, the Microsoft Store stub): use it, never a hard-coded `python3`, and give it in every message to an agent, with its scratch directory (as the preflight message below does), since agents do not read the register. Paths are in the form the register records (native on Windows, `C:/…`), the only form the allow list matches. Every script path in a command is absolute, a file of the worktree included: the interpreter rules name absolute folders, so `<python> spec-guards/lint.py` is refused where `<python> <worktree>/spec-guards/lint.py` runs. When a step says "run the lint" or "run the corpus", copy the command the register records (`Corpus`), never retype it. You are already in the worktree: no `cd … &&`, no pipes, no `env VAR=…`. Run nothing outside these forms, not even to test whether something works: the preflight probes each form, so a probe of your own adds nothing but a refusal.
- **A refusal during the audit.** A refused command is first a form to change: retry it in the form above. If that form is refused too, the launch is wrong, and every agent launched after it would fail the same way, turning its errors into UNDECIDED: launch no new agent, record the refusal (tool, command, message) in the register, set its state to `preflight failed` with the step in progress, and stop. The launcher fixes the launch as for the preflight and resumes the audit (`--resume`). Every refusal, even one fixed by a retry, is counted in the register and listed in the report: a reader must know whether a verdict was reached in a degraded environment.
- **Scratch root.** Every agent's scratch directory is under the register's `Scratch root` (`<scratch root>/iter-<k>/reviewer-a`, `…/adjudicator-F-1-3`), never under the scratchpad your own session may be offered: a replacement agent finds its predecessor's journal only there, and in the audit session the interpreter may run only there. The root depends on who holds the permissions:
  - in the audit session, `<worktree>-scratch/`, outside the worktree, so that neither git nor a reviewer browsing the worktree meets the agents' files; its allow list grants that folder, and the launcher copies there, in `protocol/`, the files the session needs from the plugin (`with_docs.py`, the report template, the corpus-errors procedure);
  - with `--in-session`, `spec-audit/<slug>/scratch/`, inside the working directory: the permissions are the user's, which commonly refuse writes outside it, and a preflight would fail on a root it cannot write. List it in `.git/info/exclude`, a local exclusion that is never committed, so that no agent file is staged; reviewers already never read `spec-audit/`. The plugin's files are used where they are, `${CLAUDE_SKILL_DIR}/references/`.
- **Register.** `spec-audit/<slug>/register.md` is the audit's memory, and nothing else is: a stop, a `--resume`, a compaction or a replacing session rereads it, not your context nor the commits. Update it after each step, as the step happens (every error entry, agent row, iteration row, revision row, digest line), never at the end.

Steps 1 to 6 prepare the audit: project rules, version convention, worktree, environment and oracle table, register, and the audit session. They are in `${CLAUDE_SKILL_DIR}/references/launch.md`: read it now, unless you are the orchestrator of an audit session, whose launcher has done them and recorded them in the register. They are kept apart because the audit session, which runs the long part of the audit, never needs them. The id of the session that loaded this skill is `${CLAUDE_SESSION_ID}`: it is the one the register's `Session` line records (step 5). Claude Code fills it in only in this file, as loaded by `/spec-audit:start`; a file read afterwards (`launch.md`, `closing.md`) or a copy of this one (the audit session's `protocol.md`) keeps the variable as written, so take the id from this sentence, and never write `${CLAUDE_SESSION_ID}` itself in the register. If this sentence shows no id, you are reading such a copy: as the orchestrator of an audit session, the launcher's id is in the register's `Session` line and yours in its `Mode` line.

**Preflight, before step 7.** Check that every tool the audit relies on actually works here, before any reviewer runs: a tool that is configured but refused turns every confirmation into UNDECIDED, and the audit is then spent for nothing. Probe what is allowed, in the forms the audit will use, and check the results yourself rather than take an agent's word for them, as for a counterexample:
1. Yourself, one probe per form of the table ("Environment"): Read and Glob in the worktree; `git status --short`; each oracle's command in a form that changes nothing (`--version`, `--help`, or a run on an empty selection); Write `<scratch root>/preflight/probe.py` (it prints `PREFLIGHT-OK`), run it with `<python> <scratch root>/preflight/probe.py`, and Read it back; run `discharge.py --help` in the form above, unless `--no-discharge`; run `arch.py check --staged …` in the form above, which must pass on an empty selection; run a corpus script, the lint once it exists, with `<python> <worktree>/<corpus>/<file>.py`; and run the probe through `with_docs.py` (`<python> <scratch root>/protocol/with_docs.py <document>=<scratch root>/preflight/probe.py -- <python> <scratch root>/preflight/probe.py`, or from `${CLAUDE_SKILL_DIR}/references/` with `--in-session`).
2. Each agent type, once, at `low` effort, with this message: "Preflight. Scratch directory: <scratch root>/preflight/<role>. Write probe.py there printing PREFLIGHT-OK, run it with <python> and its absolute path, and reply only with: preflight: ok or failed; output: <what it printed>; refused: <the exact refusal, if any>." Then check that the file exists and that its output is `PREFLIGHT-OK`.
3. Record the result in the register (`Preflight: passed`, or `failed` with the tool, the command form and the refusal, and the attempt number).
If anything fails, stop at once, before step 7, with the register's state `preflight failed`: in the audit session you cannot change your own permissions, and the launcher, which built them, fixes the launch and relaunches you (`references/launch.md`, step 6). With `--in-session`, ask the user, since they are their permissions.

7. **Inventory.** Build `spec-audit/<slug>/inventory.md`: every unit of the profile's `Inventory units` section, with its statement and the units it uses. This dependency graph serves to establish causal links (phase 3), propagate fixes (4.4) and look for errors of the same class (4.2). Unless `--no-discharge`, write with it `spec-audit/<slug>/edges.json`: for each use, the hypotheses of the used unit it relies on and where the user guarantees each, quoted, or `unstated` (`references/discharge.md`, "Edges").
8. **Baseline.** Run the whole corpus, from the worktree alone, with the oracle table's commands. It must be green; a guard already red becomes an iteration-0 error, never a test to touch up: either the document regressed or the guard is wrong, and a corpus error (4.2) decides which.
9. **Mechanical lint.** Write once in the corpus a deterministic script running the checks of the profile's `Lint` section. It feeds the editorial track. The lint reads the document through `SPEC_DOCS`, as a text guard does (`references/register.md`), so that the replay of a results folder runs it on the original as well as on the fixed copy; on the original it must go red when a form defect was fixed. Record its command in the register (`Corpus`, `lint:`), with the script's absolute path, as the preflight ran it.

## Phase 1 — Complete cold detection

All the iteration's errors are detected before any is confirmed, tested or fixed: causal sorting (phase 3) only makes sense on the full set.

Each reviewer is fresh and receives a fixed message that says nothing about the audit:

```
Review this document in full, as a referee discovering it: <paths>.
Normative dependencies (definitions it uses): <paths, or "none">.
Angle: <one of the profile's reviewer angles: full | logic and proofs | definitions, scoping and edge cases | algorithms and complexity for formal>.
Scratch directory for your computations: <scratch/iter-k/reviewer-x>.
Oracles of the project you may run for your tests: <oracle table of the register, or "none">.
Return your list in the format given by your instructions.
<the isolation line ("Roles")>
```

- The normative dependencies are those the architecture gives the document ("Project architecture"), as `arch.py normative` lists them.
- Never add the register, the corpus, previous errors, fixed areas or the reason for the audit: drawing attention to a passage already biases the review.
- The oracle table names the project's own verification artifacts (mechanized development, reference model, test runner) and their commands, which a referee would find in the repository; it says nothing about the audit, and is the reviewer's only means of execution beyond its own scripts.
- **First wave**: one full reviewer, plus angle reviewers if the document is long or dense. Each reads the whole document, because an inconsistency shows between two sections, not within one.
- **Following waves**: one fresh full reviewer. If it brings errors new to the union of the previous waves (after deduplication, phase 2), launch one more wave. Detection is complete when a wave brings nothing new, and stops at the third wave at the latest, noting then "detection not saturated" in the register.
- If the document is too long for one reading, split it by sections, but give each reviewer the definition and notation sections and the inventory's list of statements (without history), and add a pass dedicated to cross-section consistency.
- Do not modify the document during detection: all reviewers of an iteration read the same state.
- **Hypothesis discharge**, unless `--no-discharge`: alongside the waves, probe every use edge whose hypothesis the user does not visibly guarantee and that the cache has not settled for its current texts. Read `${CLAUDE_SKILL_DIR}/references/discharge.md` now: it gives the selection, the probe's message and what each verdict becomes. A red probe is a finding like a reviewer's, for phase 2.

## Phase 2 — Triage and deduplication

First classify each finding: error (definition above) or form defect (editorial track, phase 5). Style suggestions are discarded.

For each error, write a **fingerprint** independent of numbering and lines, which change with the fixes: `[type] object — defect — witness`. Example: `[false statement] bound of the partial merge — ignores the case k > n — n = 2, k = 3`.

Compare it, on meaning and not wording, with the iteration's other findings and the register's entries:

- **New** → status DETECTED, phase 3.
- **Identical to a FIXED error** → **recurrence**: stop (phase 7), without fixing again.
- **Identical to a REFUTED error** → discarded. If two independent passes still raise it, the text is misleading: open an "ambiguity" form defect to clarify it without changing its meaning.
- **Identical to an UNDECIDED or ESCALATED error** → discarded, already awaiting the user.
- **Same class, other instance** → new, linked to the original error.

## Phase 3 — Cause graph

Sort the detected errors into causal chains. An error can have several causes and consequences, so this is a directed graph: an edge `A → B` means "A causes B".

- **There is an edge `A → B`** when B's defect comes from A: B cites or applies A, or inherits its definition, and its defect would disappear if A were correct as stated; or B's counterexample is A's, or derives from it; or the same missing scoping (hypothesis, context restriction) propagates from A to B.
- **A dependency is not a causation**: there is no edge when B's own defect would remain even if A were true; B is then a root for that defect. But B still uses A, and its own fix does not cover that use: if A is confirmed, B also becomes a suspect behind A (4.1).
- Rely on the inventory and on the probable causes the reviewers report. Justify each edge in one sentence in the register.
- **Lifted counterexample**: when a red probe's counterexample also falsified results above the user (`references/discharge.md`, "Lifting"), add the edges from the user's error to each of them at once.
- **Doubtful link**: no edge, B is treated as a root, but the processing order follows the inventory's dependencies, so B comes after its presumed cause anyway.
- **Roots**: errors with no open cause.

**Causal loop.** If the graph contains a cycle (A causes B which causes A, directly or not), stop the verification: no more fixes, immediate report to the user with the cycle's errors and each edge's justification. There is no bottom to start from: either the document reasons in a circle or the causal analysis is wrong, and either way the decision belongs to a human. Redo this check whenever the graph changes (4.1, 4.4, 4.5).

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

Until its cause is fixed, a consequence is **ignored**: status BLOCKED (by F-…), neither adjudicated, tested nor fixed. Its analysis would bear on a text about to change, and its fix would risk compensating for the cause instead of repairing it.

### 4.1 Confirmation

The root goes to a fresh adjudicator with the error alone (without the reviewer's identity or the other errors), the document paths and their normative dependencies, the register's oracle table (phase 0, step 4), a scratch directory and the isolation line ("Roles"). Do not adjudicate yourself, especially an error touching a passage you fixed: you would be judging your own work. For the same reason, never run a counterexample in an adjudicator's place: if it reports that it could not execute (a tool refused, an interpreter missing), the verdict is UNDECIDED and the cause an environment problem, recorded in the register and reported, to be fixed before a fresh adjudicator is launched.

- **CONFIRMED** (with executed evidence) → mark its suspects (below), then 4.2.
- **REFUTED** (with the reason) → remove its outgoing edges; its consequences with no other open cause become roots. If the adjudicator flagged a `misleading_wording`, open an "ambiguity" form defect with it (phase 5): the passage is correct, but a referee who misread it is a reader the document will meet again.
- **UNDECIDED** (with what would settle it) → escalated to the user once no agent is running ("Questions only when idle"), no change; its consequences, suspects included, remain BLOCKED and appear in the report. Its uses are not marked as suspects: the text does not change, so there is nothing to reassess; the final report lists them as conditional results.

A user decision on an escalated error counts as the adjudicator's verdict: judged false, the error becomes CONFIRMED and its suspects are marked then; judged correct, it becomes REFUTED.

An error of type "false statement" requires an **executed** counterexample; otherwise it is downgraded to incomplete proof or UNDECIDED.

**Evidence.** The adjudicator confirms with the strongest oracle of the table covering the statement, and says which, at one of the levels of the profile's `Evidence` section, which also says when a confirmation at a weaker level than the statement allows stays UNDECIDED or is flagged. The level goes in the register (`Evidence`), and the final report counts confirmations by level. Before accepting a CONFIRMED verdict, check that its `script` exists in the agent's scratch directory and that its recorded `output` shows the failure: the adjudicator's independence is worth something only if its counterexample was run, so a verdict whose counterexample was evaluated by hand is treated as UNDECIDED (relaunch a fresh adjudicator on the same scratch directory, once).

If the adjudicator names an **upstream cause**, the root was not one: if that cause is already in the graph, add the edge; otherwise open a new error for it, in phase 3. The root goes back to BLOCKED behind its cause, and the cycle check is redone.

**Suspects.** A result C that uses A is correct if A is granted, so no reviewer flags it. Once A is confirmed false, nobody knows whether C holds until A is fixed, and a conditional result must never leave the audit presented as safe. So, as soon as A is CONFIRMED and before 4.2, every result or passage that uses A directly becomes a **suspect**, even if it is correct granting A: the union of the uses of A recorded in the inventory and of the adjudicator's `impact` field. Each suspect not already a consequence of A in the graph is added to it, with the origin `suspect (uses F-…)` in the register:

- as a consequence of A, with the edge `A → C` justified by "uses F-…, confirmed false as stated";
- with the status BLOCKED (by F-…).

A result already in the graph for its own defect, without an edge from A (phase 3), still gets this suspect entry: it is a root for its own error and a suspect behind A, and the two are settled separately.

The same rule applies when a consequence is CONFIRMED in 4.5: its own uses become suspects in turn. Propagation is thus transitive, but only along confirmed links: the uses of a suspect that turns out to hold are never marked. Redo the cycle check after these additions.

A suspect is settled only once its cause is fixed (4.5). If the cause stays unfixed (UNDECIDED, critical fix refused or pending, fix reverted after a regression), its suspects stay BLOCKED to the end of the audit, and the report lists them as results conditional on an unresolved error.

### 4.2 Documentation and guards, before the fix

Write the guard before the fix: written afterwards, it tends to test the fix rather than the error.

1. **Register**: a complete entry (format in `references/register.md`), including the probable cause (implicit hypothesis, forgotten edge case, neighboring result copied over…), which tells where to look for sibling errors.
2. **Guards**, in the corpus:
   - **Witness guard**: encodes the original statement and checks that it fails on the counterexample (documenting the error), then that the fixed statement holds on it.
   - **Variants**: at least two more cases among the relevant edge cases (empty, singleton, 0 and 1, equalities and ties, duplicates, extreme values, missing value or NULL, non-total order, overflow), and a **near-case** where the original statement is true, which protects against over-correction.
   - **Bounded check** of the fixed statement: exhaustive on a small domain, or property-based with a fixed seed.
   - **Class guard**: search the inventory for the statements exposed to the same pattern (same forgotten hypothesis, edge case or quantifier) and add a guard for each, even if correct today. A sibling statement that turns out false becomes a new error, added to the graph.
   - **Incomplete proof**: a guard on the intermediate claim of the faulty step, tested on bounded instances under the hypotheses available at that point.
   - **Text guard**, for every error: a check that reads the document itself and fails on its original wording, in its own file (`test_F_…_text.py`), so that a replay can tell it from the checks of the encoded statement. It asserts what the fix changes in the text: the original wording absent and the fixed one present, the corrected value of an example, the hypothesis added to a statement, the justification added to a proof step. The other guards check an encoding of the statement, which stays green if someone reverts the text; only this one sees the document go back. It reads the document through `SPEC_DOCS` (format in `references/register.md`), so that the same corpus runs on the project and on the original and fixed copies of a results folder (8.4). A critical fix still pending has no text guard yet: there is no fixed text to assert.
3. **Red first**: run the guard against the original wording: the assertion on the original statement must fail, proving that the guard detects the error, and the text guard must fail on the original document. Record the result in the register.

Corpus rules:
- it only grows: never delete or loosen a guard to make it pass; a guard changes only through a corpus error (below), justified in the register and flagged in the report;
- the model encoded in the guard follows the document's definitions, not the proposed fix;
- follow the conventions of the existing corpus (headers, naming, test runner);
- a guard is written for the oracle that confirmed the error, at its level, in the form the profile's `Guards` section gives (arithmetic, language of the guard, what "red first" and "green" mean for that oracle); a guard for an oracle goes where the architecture's `Guards` cell of that oracle says (a Lean guard module in `mechanization/Guards/`, for instance), the others in the corpus.

**Corpus errors.** A guard can be wrong as well as the document: too strict (it rejects a valid fix), badly encoded (it models a definition differently from the text, so it can confirm a false error or miss a real one), or empty (it passes whatever the text says). Nobody else reads the guards: the reviewers never see the corpus, by design, and you write both the guards and the fixes. Changing a guard on your own judgment would be judging your own work, so a suspect guard follows the same path as a suspect statement: The procedure (report, adjudicate, settle, and what to do with the project's own tests) is in `${CLAUDE_SKILL_DIR}/references/corpus-errors.md`: read it as soon as a guard is suspect, that is, when it stays red on a fix you consider valid, stays green on the original wording, is flagged `NO TEXT CHECK` by a replay, or is red at the baseline (phase 0, step 8). Until it is settled, do not touch the guard, and the fix or the error it guards stays where it was.

### 4.3 Fix

Choose the nature of the fix, and record it:

- **statement fix**: the conclusion is weakened or corrected;
- **scoping addition**: a hypothesis is added, or the context or domain of application is restricted, so that the statement becomes true again;
- **proof completion or repair**: the statement holds, the faulty step is justified or replaced.

They can be combined if needed. In all cases:

- **Minimal fix**: the weakest change that makes the statement true and keeps its uses valid. Never strengthen a statement, do not introduce a new result to plug a gap, never delete a result silently: a withdrawn result is marked as such, with the reason and the counterexample.
- **Critical fixes**: changing the statement of a main result (theorem, result cited in the abstract) or withdrawing a result changes what the document claims. A main result is one the document presents as such: a theorem, or a result that the abstract or the conclusion names or states itself. Judge the statement being fixed, not what depends on it: a lemma whose consequence appears in the abstract is not critical on that account. Its fix is the cause, made like any other; the passage of the abstract or conclusion stating the consequence is the critical fix, presented to the user. This keeps the bottom-up order and puts the human decision where the document makes its claim; gating the lemma instead would block its whole chain on a question the user is not asked directly. By default, first handle the non-critical roots, then, once no agent is running ("Questions only when idle"), present the pending critical fixes to the user together (statement before and after, counterexample, impact) and wait for their approval; their chains, suspects included, remain BLOCKED until then, and stay BLOCKED if the user refuses. With `--auto`, apply them and flag it in the report.
- **Green**: run the error's guard, then the whole corpus. A green guard that turns red is a regression: revert the fix and set the error back to UNDECIDED; its consequences and suspects stay BLOCKED.
- **Internal revision**: once the error is FIXED, commit in the worktree the document, its guards and the register as internal revision r<N>. The register must first hold the error's complete entry (with its guards' red and green results), the agent table rows of the agents involved, and the revision's row: a resume, a stop or a replacing session rereads the register, not the commits, so a revision whose register lags behind the document is not a verified state. Stage by path (the document, the guard sources, the register, the inventory and `edges.json`, its quotes updated to the fixed text), never a whole folder, run the architecture check ("Standing rules"), and check `git diff --cached --stat`: test runners leave caches and bytecode beside the guards (`__pycache__/`, `.pytest_cache/`), which do not belong in the corpus and would bury its diff. Revisions are numbered from 1 over the whole audit, and the message marks them incomplete: `spec-audit(<slug>): r<N> — F-… fixed [incomplete: audit in progress]`. Each revision is a verified state, every guard green, to which a stop or an interruption can return without losing the fixes already made; it is incomplete because the error's consequences may not have been reassessed yet. The mark stays in the commit message and the register, never in the document: the reviewers read the document and must not learn that an audit is running.
- **Traceability**: if the document has an errata, history or revision section, or if the project versions its documents, record the fix according to that convention.
- **Profile rules**: apply the profile's `Fixes` section (for `formal`, the fix of a mapped statement includes its formal counterpart, in the same internal revision).

### 4.4 Propagation

Starting from the inventory, recheck everything that depends on the fixed statement: later results, proofs that cite it, examples, tables, abstract, introduction, conclusion, other project documents, code or mechanization that refer to it. This covers every use, including those without an edge in phase 3: a result with its own defect still uses the statement, and the fix can break it in another way. What a use must still get from the fixed statement depends on the nature of the fix:

- **statement fix**: the conclusion has changed, so every use that relied on the original conclusion becomes a new error, unless the fixed conclusion still gives it what it needs;
- **scoping addition**: every use must satisfy the new hypothesis; a use that no longer does becomes a new error; add each use to `edges.json` with the new hypothesis, so that the next iteration probes the ones it cannot settle by a quote;
- **proof completion or repair**: the statement is unchanged, so its uses are not affected.

A new error is a consequence of the root (edge root → new error), handled in the same loop. Uses already in the graph as suspects are not duplicated: their reassessment (4.5) settles them. Propagation catches the uses that the inventory and the adjudicator missed when the suspects were marked.

### 4.5 Reassessment of consequences

When all the causes of a consequence are handled, send it to a fresh adjudicator, who judges it against the fixed text. Suspects are reassessed the same way.

**Handover: only what the next link needs.** The message gives the consequence or suspect (location and quote), the passage of its cause as it reads now, the document paths, the oracle table, a scratch directory and the isolation line, and asks whether the result holds against that text. It never carries the cause's history: neither its original wording, its counterexample, the earlier adjudicator's reasoning, its guards, nor the fact that it was fixed. That history would cost tokens at every link of a long chain, and above all it would bias the judgment as it would a reviewer's: an adjudicator told that its cause was false looks for the same defect, rather than reading the result against the text as it is. To limit the cost, a single fresh adjudicator can reassess all the suspects of the same cause, with one verdict per suspect: they all read the same fixed passage.

- **REFUTED** → status RESOLVED (by F-…); for a suspect, the result holds against the fixed text. Add its case to the cause's guards: if the cause regressed, the consequence would show it too.
- **CONFIRMED** → it becomes a root and follows the full protocol (4.2 to 4.4); its own uses become suspects in turn (4.1).
- **Change of nature** → new error, added to the graph.

**Proof repaired, statement unchanged.** If the cause was an incomplete proof repaired without any change to its statement, its suspects go straight to RESOLVED (by F-…), without adjudication: they were only conditional on the repair, and nothing they use has changed.

## Phase 5 — Editorial track

After the iteration's substantive fixes, which can move the text and the numbers:

- rerun the lint and fix what it reports;
- fix typos outside formulas (spelling, grammar, layout); any change to a formula, symbol, index, quantifier or inequality is an error, not a form defect;
- **numbering**: prefer stability (insertion as 4.3′ or 4.3a). If renumbering is unavoidable, update all cross-references, internal and external, and record the old → new mapping;
- **bibliography**: only fix a reference against its source (the architecture's `sources`, a local PDF, publisher's page, DBLP…), never the source itself; otherwise mark it "to be checked" and leave it as is. Never invent metadata: pages, DOI, theorem number;
- for each class of defect fixed, add a lint rule, so that it is detected mechanically from now on.

## Phase 6 — End of iteration

Run the whole corpus and the lint: everything must be green. Unless `--no-discharge`, record the iteration's probes in the cache (`references/discharge.md`, "Record"). Commit locally in the worktree (message listing the identifiers of the errors and defects handled), only your files, after the architecture check ("Standing rules"), without pushing; this commit is also an internal revision (4.3). Update the register's log.

## Phase 7 — Loop and stop

Go back to phase 1 with new agents. Stop at the first condition met:

1. **Convergence**: a complete cold detection produces no confirmed error. If the previous iteration changed the statement or the scoping of a result, require a second clean detection: that is where new errors are born.
2. **Causal loop**: the cause graph contains a cycle (phase 3).
3. **Recurrence**: an error is identical to an already FIXED error. Stop without fixing again: either the fix did not hold, or two fixes contradict each other. Report both entries and the diff at fault.
4. **Oscillation**: a proposed fix would undo, even partially, an earlier fix of the audit; or the same fix has produced two successive confirmed errors.
5. **Non-convergence**: the number of confirmed errors does not decrease over two consecutive iterations. The document probably needs human rework rather than patches.
6. **Budget**: `--max-passes` reached.
7. **Exhaustion**: detection only finds form defects. Finish the editorial track, rerun the lint and the corpus, then stop.
8. **First error**, with `--fail-fast`: an error is CONFIRMED ("Fail-fast").

Never conclude "the document is correct". Conclude "N independent detections found no further confirmed error", stating what was not checked.

## Fail-fast

With `--fail-fast`, the audit answers one question, cheaply: does the document hold an error a reader can be shown? It runs one pass, and changes the phases as follows; everything else holds (independence of the agents, executed counterexamples, register).

- **Phase 0**: no lint (step 9): it only feeds the editorial track, which a fail-fast audit skips.
- **Phase 1**: one full reviewer, launched as soon as the inventory is written, before `edges.json`, then hypothesis discharge, its probes joining the candidates as they arrive; no angle reviewers and no further wave. The register notes "detection not saturated (fail-fast)".
- **Phases 2 and 3** as usual: the cause graph orders the candidates.
- **Phase 4**: confirmation only (4.1), one candidate at a time, the roots first in the inventory's dependency order, so that the first error confirmed is most likely a cause rather than a consequence. A candidate whose adjudicator names an upstream cause is followed by that cause, as 4.1 says. A REFUTED candidate frees its consequences, which become roots in turn; an UNDECIDED one is listed and skipped, without a question. On the first CONFIRMED verdict, complete its register entry (counterexample, evidence, the adjudicator's minimal fix and impact), list its suspects without adjudicating them, and stop: no guard, no fix, no internal revision. The document is not changed: a fix nobody reviews would be worse than none, and the full audit that follows will make it with its guards.
- **Phases 5 to 7**: no editorial track; commit the register and the inventory (`spec-audit(<slug>): stopped at first error F-…`), and stop, by condition 8, or with no error confirmed once no candidate is left.

`--max-passes` and `--auto` do not apply: there is one pass, and nothing is fixed.

## Final report

Write it in `spec-audit/<slug>/report.md`, from the register, when phase 7 stops the audit. Its template, the rules for conditional results and for the summary of issues that ends it, and what it must never claim, are in `${CLAUDE_SKILL_DIR}/references/report.md`: read it then. Kept apart because it is needed once, at the very end, and every word of it would otherwise stay in context during the whole audit.

## Phase 8 — Closing

Closing is decided with the user once the report is written: classify the outcome, present the report, ask the closing question, build the results folder and its index entry, then merge, keep or abandon; and the stop on request. It is in `${CLAUDE_SKILL_DIR}/references/closing.md`: read it when the report is written, or when the user asks to stop the audit. It is kept apart because only the launcher, or you with `--in-session`, ever runs it: the audit session ends with its report.
