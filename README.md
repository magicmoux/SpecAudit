# SpecAudit

**A Claude Code plugin for iterative precision audits of theoretical, technical and mathematical specifications.**

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Version 0.7.1](https://img.shields.io/badge/version-0.7.1-informational.svg)
![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A63D2.svg)

SpecAudit audits formal documents — papers, proofs, algorithm, protocol or format specifications — for logical, mathematical and algorithmic errors. Fresh reviewer agents with no history detect the errors; an independent adjudicator agent confirms each one with an executed counterexample; confirmed errors are ordered into a cause graph and fixed bottom-up, each fix being preceded by a regression guard in a growing test corpus. The whole audit runs in a dedicated git worktree and ends with a report and a multiple-choice closing question.

## Why

An author cannot see their own blind spots, and a reviewer who knows the history reads what they expect to read. `spec-audit` therefore separates the roles: fresh reviewers who know nothing about the audit, an adjudicator who confirms or refutes each error, and an orchestrator who keeps the register, sorts the errors, writes the guards and makes the fixes.

Three principles guide everything else:

- **An unconfirmed error is not an error.** Reviewers produce false positives, and fixing a correct statement damages the document as much as leaving a false one.
- **Fix a cause before its consequences.** Fixing a consequence first masks the cause, or compensates for it in the wrong place.
- **An error fixed without a guard will come back.** Every fix leaves a test in the corpus that would fail if the error reappeared.

## Features

- **Cold detection**: fresh `spec-reviewer` agents, with no history and no register, review the whole document in waves until a wave brings nothing new.
- **Confirmation by execution**: a fresh `spec-adjudicator` agent first tries to refute each error, then to confirm it with a minimal executed counterexample, on the strongest oracle of the project that covers the statement: mechanized development (Lean, Coq…), reference model, or its own script as a last resort; every confirmation carries its evidence level.
- **Cause graph**: errors are sorted into causal chains and fixed bottom-up; a consequence stays blocked until its cause is fixed, and a causal loop stops the audit.
- **Regression guards**: a witness guard written and seen red before the fix, variants on edge cases, a near-case against over-correction, a bounded check, class guards for sibling statements; each one written for the oracle that confirmed the error, a Lean theorem included.
- **Minimal, traced fixes**: statement fix, scoping addition or proof repair; never a strengthening, never a silent deletion; critical fixes wait for your approval.
- **Separate editorial track**: typos, numbering, cross-references and bibliography, with a mechanical lint that grows with each class of defect fixed.
- **Git isolation**: everything happens in an `audit/<slug>` worktree, with local commits, without touching your working directory and without ever pushing.
- **A session of its own**: by default the audit runs in a dedicated `claude -p` session started in the worktree, with none of your plugins, skills, connectors, hooks or memory, allowed to run exactly git and the project's oracles; `--in-session` keeps it in your session.
- **Explicit stop conditions**: convergence, budget, recurrence, oscillation, non-convergence, causal loop or exhaustion.
- **You decide the closing**: full report, then a multiple-choice question (accept and merge, run another check, keep, abandon), the safest option being recommended.
- **Stop at any time**: `/spec-audit:stop`, from the session that launched the audit, stops it with its agents and reports its last internal revision, a verified but incomplete state committed after each fixed error; you then suspend the audit, keep that revision as the new base, or cancel.

## Installation

In Claude Code:

```text
/plugin marketplace add magicmoux/SpecAudit
/plugin install spec-audit@spec-audit
```

Or from the command line:

```bash
claude plugin marketplace add magicmoux/SpecAudit
claude plugin install spec-audit@spec-audit
```

Installation for a project or a team, from a local clone, or without the plugin system: see [docs/installation.md](docs/installation.md).

## Quick start

From the git repository that contains the document:

```text
/spec-audit:start docs/specification.md
```

The skill also triggers on natural-language requests, for example: "Check the proofs in `docs/specification.md` before submission."

To watch a complete audit at no risk, run it on the demo specification in [examples/](examples/), which contains known errors.

## Parameters

| Parameter | Effect |
|---|---|
| `<document>` | the audited file or files |
| `--corpus <dir>` | global guard corpus (default: the project's verification corpus, otherwise `spec-guards/`) |
| `--max-iter N` | maximum number of iterations (default: 5) |
| `--auto` | also apply critical fixes without waiting for your approval |
| `--resume` | resume an interrupted audit in its worktree |
| `--base <ref>` | starting branch or commit of the worktree (default: `HEAD`) |
| `--no-worktree` | work in place, without a worktree |
| `--in-session` | run the orchestrator in your session instead of a session of its own |
| `--model <family\|id>` | model of the audit session and of its agents (default: your session's family) |
| `--model-version <v>` | version of that family (default: `latest`) |
| `--keep` | ask no question at closing and keep the worktree |

Details and examples: [docs/usage.md](docs/usage.md).

## What an audit produces

In the worktree `<repository>-audit-<slug>`, on the branch `audit/<slug>`:

- the fixed document, one fix per confirmed error, committed locally;
- `spec-audit/<slug>/register.md`: the audit's memory (log, cause graph, each error with its counterexample, verdict, guards and fix);
- `spec-audit/<slug>/inventory.md`: definitions, results and their dependencies;
- `spec-audit/<slug>/report.md`: the final report;
- the guard corpus and the lint script, replayable at any time.

Whatever the outcome, the report comes back to the session and to the original branch; if you do not merge, a `corrections.patch` is archived with it.

## Requirements

- Claude Code with plugin support;
- git (the document must be in a repository, otherwise the skill offers to initialize one);
- a model for the agents: they inherit the audit session's, your session's by default, or the one given with `--model` and `--model-version`;
- the `claude` CLI on your `PATH`, for the default mode (the audit runs in a session of its own); `--in-session` does without it;
- an interpreter to run counterexamples and guards: Python 3 by default, or the project's own oracles (mechanized development, reference model, test runner).

An audit launches several agents per iteration: it consumes a lot of tokens. `--max-iter` bounds the spending.

## What the audit does not guarantee

Review by agents and bounded tests are neither peer review nor proof. The audit never concludes "the document is correct", but "N independent detections found no further confirmed error", stating what was not checked. Only a mechanized proof can be called machine-verified.

## Documentation

- [Installation](docs/installation.md): installation modes, checking, updating, uninstalling, troubleshooting.
- [Usage](docs/usage.md): launching, parameters, workflow, output files, closing, resuming.
- [How it works](docs/how-it-works.md): roles, phases, cause graph, guards, stop conditions.
- [Audit profiles](docs/profiles.md): design of the domain profiles (formal today; functional, UI, research and experimental planned).
- [Example](examples/): demo specification with known errors.
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md).

## Repository layout

```text
SpecAudit/
├── .claude-plugin/
│   ├── plugin.json            plugin manifest
│   └── marketplace.json       the repository is also a marketplace
├── skills/
│   ├── start/
│   │   ├── SKILL.md           /spec-audit:start, orchestrator: phases 0 to 8
│   │   ├── references/
│   │   │   └── register.md    formats of the register, its entries and the guards
│   │   └── profiles/
│   │       └── formal.md      rules specific to formal documents
│   └── stop/
│       └── SKILL.md           /spec-audit:stop, stops the audit running in the session
├── agents/
│   ├── spec-reviewer.md       fresh reviewer, no history
│   └── spec-adjudicator.md    adjudicator: refute first, then confirm by execution
├── docs/                      installation, usage, how it works
├── examples/                  demo specification
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

## License

[MIT](LICENSE).
