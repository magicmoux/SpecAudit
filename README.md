# SpecAudit

**Catch the errors in your specs before your readers do.** SpecAudit reviews them like a skeptic, and confirms an error only with evidence you can rerun. Formal documents today; other kinds of spec planned, open to contributions.

[![License: PolyForm Shield 1.0.0](https://img.shields.io/badge/license-PolyForm%20Shield%201.0.0-lightgrey.svg)](LICENSE)
![Version 1.0.0-beta.4](https://img.shields.io/badge/version-1.0.0--beta.4-orange.svg)
![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A63D2.svg)

SpecAudit audits documents that make claims a reader can check, and fixes the errors it can prove. Its core does not depend on the domain; what counts as an error, as evidence and as a guard comes from an **audit profile**, one per kind of document. **Only the `formal` profile is implemented so far**: papers, proofs, algorithm, protocol or format specifications, audited for logical, mathematical and algorithmic errors. Profiles for functional specifications and requirements, UI specifications, research positioning and experimental protocols are planned, and open to contributions ([Future work](#future-work-up-for-grabs)); until they exist, a non-formal document is audited with the formal rules, which suit it poorly ([Limits](#limits-risks-and-side-effects)).

Fresh reviewer agents with no history detect the errors; an independent adjudicator agent confirms each one with an executed counterexample; confirmed errors are ordered into a cause graph and fixed bottom-up, one at a time, each verified on the current revision and each fix being preceded by a regression guard in a growing test corpus. The whole audit runs on a branch of its own, in a dedicated git worktree, and ends with a final commit on that branch, which it never merges, a report and a multiple-choice closing question.

The `formal` profile is in beta: to take part, see [Beta testing](#beta-testing).

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
- **Regression guards**: a witness guard written and seen red before the fix, variants on edge cases, a near-case against over-correction, a bounded check, class guards for sibling statements; each one written for the oracle that confirmed the error, a Lean theorem included; and a **text guard** that reads the document itself, so that a reverted text turns the corpus red, not only a wrong encoding of the statement.
- **Guards are checked too**: a guard suspected of being wrong is never edited by the orchestrator, which writes the fixes as well; a fresh adjudicator judges it against the text, and a replacement must be seen red first.
- **Minimal, traced fixes**: statement fix, scoping addition or proof repair; never a strengthening, never a silent deletion; critical fixes wait for your approval.
- **Separate editorial track**: typos, numbering, cross-references and bibliography, with a mechanical lint that grows with each class of defect fixed.
- **Your project's architecture, followed**: `/spec-audit:init` proposes `SPECAUDIT_ARCH.md`, the role of each part of the repository, which you confirm or adjust; the audit changes only the documents marked audited (and a mapped formal counterpart with its statement), leaves originals, normative references, sources and oracles alone, and refuses to run without the file.
- **Git isolation**: everything happens on a branch `audit/<stamp>`, named like the audit's results folder, checked out in a worktree of its own, with local commits, without touching your working directory, without ever merging and without ever pushing.
- **One agent at a time, on a known revision**: agents run one after the other, never side by side, so none races another on an oracle, a file or a text being fixed; every error is verified on the revision its predecessor's fix left, and every verdict records the commit it was reached on.
- **A session of its own**: by default the audit runs in a dedicated `claude -p` session started in the worktree, with none of your plugins, skills, connectors, hooks or memory, allowed to run exactly git and the project's oracles; `--in-session` keeps it in your session.
- **Explicit stop conditions**: convergence, budget, recurrence, oscillation, non-convergence, causal loop or exhaustion.
- **You decide the closing**: full report, ending with a summary of issues by priority, each with its mitigation and an effort range in person-days when something supports one; then a multiple-choice question (keep the branch, run another check, abandon), the safest option being recommended. The audit never merges its branch: you merge it, or not, by your own means.
- **A self-contained, indexed result**: every audit run to completion leaves `SpecAudit-<YYYYmmdd_HHmmss>/` at the root of the project, with the sources as they were, the report, the fixed document when no error stays open, and a corpus that replays on either version; `SPECAUDITS.md` has an entry for every audit launched, from its launch to its result, linked to a section that summarizes it.
- **Attestation you control**: `/spec-audit:attest` checks the signed git tag with which you stand by a result; the audit never signs in your name.
- **Context economy**: each agent gets only what its step needs, the orchestrator carries a one-line digest per settled error, and the protocol is loaded in parts, so that long audits stay affordable.
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

From the git repository that contains the document, first describe the project's architecture, once:

```text
/spec-audit:init
```

It proposes a role for each part of the repository (the documents to audit, earlier versions, normative references, sources, verification artifacts such as a Lean development, what to ignore), asks you to confirm or adjust, and writes `SPECAUDIT_ARCH.md`. The audit refuses to run without it. Then audit:

```text
/spec-audit:start docs/specification.md
```

The skill also triggers on natural-language requests, for example: "Check the proofs in `docs/specification.md` before submission."

To watch a complete audit at no risk, run it on the demo specification in [examples/](examples/), which contains known errors.

## Beta testing

The `formal` profile is in beta. Testers install the plugin from this repository, run it on the demo and then on formal documents of their own, and report what the audit missed, what it got wrong and what it cost.

**Install.** In Claude Code:

```text
/plugin marketplace add magicmoux/SpecAudit
/plugin install spec-audit@spec-audit
```

The maintainer announces each beta round. When a round is announced with a tag, add the marketplace at that tag instead, so that every tester runs the same version, for example `/plugin marketplace add magicmoux/SpecAudit#v1.0.0-beta.1`: a marketplace added with `#<ref>` follows that ref ([release channels](https://code.claude.com/docs/en/plugins/host-marketplace#run-release-channels)).

**Update.** Auto-update is off by default for third-party marketplaces. Update by hand:

```bash
claude plugin marketplace update spec-audit
claude plugin update spec-audit@spec-audit
```

or enable auto-update under `/plugin` → Marketplaces. A new copy is installed only when `version` in `plugin.json` changes.

**First test: the demo.** Run the audit on [`examples/demo/bubble-sort.md`](examples/demo/bubble-sort.md) as [examples/README.md](examples/README.md) describes. It checks the installation, and its planted errors and the two real runs in [examples/demo-result/](examples/demo-result/README.md) make reports comparable.

**What to test.** Real formal documents of your own: proofs, algorithms, protocol or format specifications. Begin with `--fail-fast`, which stops at the first confirmed error and reports its proposed fix and the results it may affect, then run full audits, with a few pages and `--max-passes 1` first, then longer ones. Non-formal documents are out of scope of this beta: only the `formal` profile exists, and it suits them poorly ([Limits](#limits-risks-and-side-effects)).

**One audit at a time.** Several audits at once in the same repository work: each runs on its own branch, in its own worktree, and they share only the index `SPECAUDITS.md` and the results folders at the root of the original branch, whose writes are serialized. But this is not yet validated beyond the tests, so for this beta, run one audit at a time per repository.

**Cost.** Measured on the demo, an audit costs about $0.50 to $2.50 with Sonnet, depending on the mode (audit session by default, or `--in-session`). A real document costs several times more; `--max-passes` bounds the spending.

**How to report.** Open a [beta report](https://github.com/magicmoux/SpecAudit/issues/new?template=beta-report.yml). The most useful reports name an error the audit missed, a fix you contest, or a real error it judged false or left UNDECIDED, with the passage before and after.

**Confidentiality.** A results folder `SpecAudit-<stamp>/` contains the audited document: `source/`, the fixed copy and `resources/corrections.patch`. Never attach it for a confidential document. Share instead the document's entry in `SPECAUDITS.md`, the report's "Summary of issues" and the excerpts you choose.

## Parameters

| Parameter | Effect |
|---|---|
| `<document>` | the audited file or files, or a folder, for the documents it contains; each must be `audited` in `SPECAUDIT_ARCH.md` (`/spec-audit:init`) |
| `--corpus <dir>` | global guard corpus (default: the project's verification corpus, otherwise `spec-guards/`) |
| `--max-passes N` | how many times the document is audited at most: audited, fixed, then audited again as fixed (default: 5) |
| `--auto` | also apply critical fixes without waiting for your approval |
| `--resume` | resume an interrupted audit in its worktree, with its recorded parameters; `--max-passes`, `--auto`, `--pause-at`, the model and a few others may be changed, not what is audited ([usage](docs/usage.md)) |
| `--base <ref>` | starting branch or commit of the worktree (default: `HEAD`) |
| `--no-worktree` | work in place, without a worktree |
| `--in-session` | run the orchestrator in your session instead of a session of its own |
| `--model <family\|id>` | model of the audit session and of its agents (default: your session's family) |
| `--model-version <v>` | version of that family (default: `latest`) |
| `--keep` | ask no question at closing and keep the branch (the results folder still comes back) |
| `--uniform-effort` | launch every agent at its usual effort, without per-step routing |
| `--account <email>` | the account the audit session is billed to: checked instead of asking at launch, required where no question can be asked |
| `--pause-at <N \| session=N,week=N \| off>` | pause at N % of the account's session window or week (default `session=75,week=50`), and resume when it resets |
| `--no-auto-resume` | on a pause, stop instead of waiting for the session window to reset |
| `--fail-fast` | stop at the first confirmed error, without fixing it; the report gives its proposed fix and the results it may affect |
| `--no-discharge` | skip hypothesis discharge, the probes of each use edge |

Details and examples: [docs/usage.md](docs/usage.md).

## What an audit produces

In the worktree `<repository>-audit-<slug>`, on the branch `audit/<stamp>`:

- the fixed document, one fix per confirmed error, each committed as an internal revision, then a final commit at closing;
- `spec-audit/<slug>/register.md`: the audit's memory (log, cause graph, each error with its counterexample, verdict, guards and fix);
- `spec-audit/<slug>/inventory.md`: definitions, results and their dependencies;
- `spec-audit/<slug>/report.md`: the final report, with what the audit consumed: tokens per agent, cost, and its share of your account's session and week windows;
- the guard corpus and the lint script, replayable at any time.

Whatever the outcome, the report comes back to your session. Every audit run to completion also leaves a results folder at the root of the project, named by the time you launched it, and comes back to your branch with it:

```text
SpecAudit-20261010_210233/
├── README.md            outcome, sources (repository, branch, commits), contents, tests, attestation
├── report.md            the report, and annex-*.md when a section is long
├── register.md          the register, as closed
├── inventory.md
├── selection.fixed.md   the fixed document, only when no error stays open
├── source/              the audited files as they were at the start
├── docs/                documents consulted, bibliography
└── resources/           corpus, replay.py, corrections.patch, executed counterexamples
```

`SPECAUDITS.md`, at the root, has an entry for every audit launched, newest first: a summary table (date, audited object, launched by, result: `RUNNING`, `FINISHED`, `INTERRUPTED` or `FAILED` with its detail), linked to one section per audit with its summary, details (its consumption among them) and results folder. To attest a result, sign a git tag on your own machine after reading the report; `/spec-audit:attest` checks it.

## Audit monitor (optional, experimental)

> **Experimental.** The monitor is still being developed outside this repository; the version here is an early snapshot (0.14.4), which may change a lot or be replaced as a whole when it reaches its first stable version. Install it to try it, not to rely on it; `spec-audit` does not need it.

`specaudit-monitor` is a separate, optional plugin of the same marketplace: a band above the prompt and a detail pane that follow the audit of the current project.

```text
/plugin install specaudit-monitor@spec-audit
```

- The band, on two lines: first the icon, `SpecAudit`, the audited document, the audit's stage as one coloured glyph (`●` running, `⏸` suspended, `⏹` stopping, `?` waiting on a decision, `✔` done; in words in the pane) and, at its right end, `⤢`, which opens the pane, as `/specaudit-pane` does; then, while a usage window has used 70 % or more of its margin to the pause threshold, one alert line per window (red from 90 %); then a spinner while it works (`⏸` once suspended), its progress (errors evaluated out of those detected) and how much of the usage margin, from the launch to the pause threshold, the audit has used, for the session and week windows side by side; once the audit has ended, its final figures (confirmed and fixed errors, guards, result), kept until the next one, with its controls at the right end as glyphs alone.
- Another repository: each write of an index (`index.py`) leaves a beacon, `~/.specaudit/beacon.json`, naming its repository, and the monitor follows that repository's audit when it is live, or newer than the current project's, so that an audit launched elsewhere (an end-to-end test's throwaway repository) shows without changing folder. Without the monitor, nothing reads the beacon, and a beacon that cannot be written changes nothing.
- The band's buttons, on the audit it shows, in that audit's own repository: `⏸` (pause) and `⏹` (stop) while it runs in its own process (not with `--in-session`), `▶` (resume) once it is suspended; a control the audit's state does not allow is not drawn, and the band follows that state at each refresh. An audit the register says is going whose process has ended, or a suspended one whose launcher session is no longer running (no process runs it: its id after `--resume` or `--session-id`), shows as stopped (`⏹`, `Arrêté : …` in the pane), without controls, except `▶` for a suspended one: with its launcher gone, `▶` does what `/spec-audit:start <document> --resume` typed in this session does, and this session becomes the audit's launcher; that takes a session opened in the audit's repository with the start skill installed, otherwise a toast says where to run the command. Pause and stop write `stop-requested` in the audit's scratch root, the stop of `closing.md` 8.9: the running agent reports its state and the audit suspends. Pause then tells the session that launched the audit to leave it suspended; stop, on a second press within 10 s (its glyph turns red after the first), asks that session to run `/spec-audit:stop`, which asks how the audit ends. Resume asks that session for `/spec-audit:start <document> --resume`. When that session is not running, a toast gives the command to run.
- The pane: consumption first (tokens, cost, session and week windows), then sections folded by default: progress, errors (a table with each error's status and notes, a row opening its card), evidence, and technical details.

It reads the audit's register, `SPECAUDITS.md`, git and the audit session's stream; it writes only the audit's `stop-requested`, and messages the session that launched the audit, on a press of its buttons. It never calls a model and costs no tokens itself. It relies on Claude Code's mod API, which may change between Claude Code versions; if it does, only the monitor stops loading, never `spec-audit`. Its sources and tests are in [`mods/specaudit-monitor/`](mods/specaudit-monitor/); its interface is in French for now.

## Requirements

- Claude Code with plugin support;
- git (the document must be in a repository, otherwise the skill offers to initialize one);
- a model for the agents: they inherit the audit session's, your session's by default, or the one given with `--model` and `--model-version`;
- the `claude` CLI on your `PATH`, for the default mode (the audit runs in a session of its own); `--in-session` does without it;
- an interpreter to run counterexamples and guards: Python 3 by default, or the project's own oracles (mechanized development, reference model, test runner).

An audit launches several agents per pass: it consumes a lot of tokens. `--max-passes` bounds the spending.

## Limits, risks and side effects

**What the result is, and is not.** Review by agents and bounded tests are neither peer review nor proof. The audit never concludes "the document is correct", but "N independent detections found no further confirmed error", stating what was not checked. Only a mechanized proof can be called machine-verified. In particular:

- **An error no reviewer finds is not reported.** Guards and counterexamples check the cases they encode, often small ones; a statement that passes them is not thereby true.
- **An adjudicator can be wrong both ways.** Most confirmations rest on a script an agent wrote and ran; the report says, for each, what it rests on (`ad hoc`, a reference model, a mechanized proof).
- **Two runs are not identical.** On the same document, two audits find the same substantive errors as a rule, but may word, order or fix them differently, and may judge differently whether a fix is critical (and so waits for you).
- **A valid fix is not always the one you would choose.** An audit may withdraw a result rather than restate it, reword a correct proof to make it clearer, or narrow a statement where you would have added a hypothesis. Each change is listed under "Modified statements" in the report, and their review by the author is a row of the summary of issues: read them before you merge.
- **Only formal documents are audited as they should be.** A functional specification, a requirements document or a UI specification is audited today with the formal profile: most findings then end UNDECIDED, since a false statement demands an executed counterexample that such documents rarely allow, and genuine defects (an untestable requirement, two contradictory screens) are filed as form defects. The profiles that fix this are [future work](#future-work-up-for-grabs).
- **Not for refereeing.** Do not use SpecAudit on a manuscript submitted to you for review: sending a confidential submission to an AI service breaks the confidentiality of peer review, and many journals forbid it. The intended use is an author auditing their own text.
- **Effort estimates are indicative ranges**, with their basis and a confidence; the audit knows neither your team nor its pace.

**What an audit does to your project.** It creates a branch `audit/<stamp>` and its worktree next to your repository, a guard corpus (`spec-guards/` by default) on that branch, the index `SPECAUDITS.md` and a results folder `SpecAudit-<stamp>/` at the root. It commits on your current branch twice, and only these two: the index entry at launch, the results folder and the index at closing; both name the audit's branch and its final commit. The fixes stay on `audit/<stamp>`: the audit never merges it, nor proposes a merge or a pull request; you review it and merge it, or not, by your own means. It never pushes, and never signs.

**What it runs.** The agents write and run scripts (counterexamples, guards) on your machine, with the permissions of the session, restricted in the default mode to the command forms the protocol lists. An audited document is input the agents read and act on: audit documents whose origin you trust, or run the audit in a container or a throwaway clone.

**What it costs and where your text goes.** An audit launches several agents per pass and consumes a lot of tokens: the demo costs about $0.50 to $2.50 with Sonnet depending on the mode, a real specification several times more; `--max-passes` bounds the spending. The document and what the agents produce go to the model provider like any Claude Code session.

**Who launched it.** "Launched by" is the git identity of the session, which anyone can set: it says who ran the audit, not who stands by its result. Only a signed tag checked by `/spec-audit:attest` does that.

### Disclaimer

SpecAudit is provided **as is**, without warranty of any kind, express or implied, as stated in its [license](LICENSE) (the "No Liability" section of PolyForm Shield 1.0.0). You use it **at your own risk**. It does not replace review by a qualified person: you remain responsible for the documents you publish or rely on, for reviewing every change it proposes before you merge it, and for the cost of the runs you launch. Its authors and contributors are not liable for any claim, damage or loss arising from its use, including from an error it missed or a fix it introduced.

## Documentation

- [Installation](docs/installation.md): installation modes, checking, updating, uninstalling, troubleshooting.
- [Usage](docs/usage.md): launching, parameters, workflow, output files, closing, resuming.
- [How it works](docs/how-it-works.md): roles, phases, cause graph, guards, stop conditions.
- [Audit profiles](docs/profiles.md): design of the domain profiles (formal today; functional, UI, research and experimental planned).
- [Example](examples/): demo specification with known errors.
- [Eval suite](evals/README.md): behavioral tests of the plugin, and how to run them.
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md).

## Repository layout

```text
SpecAudit/
├── .claude-plugin/
│   ├── plugin.json            plugin manifest
│   └── marketplace.json       the repository is also a marketplace
├── skills/
│   ├── init/
│   │   ├── SKILL.md           /spec-audit:init, proposes the project's architecture, SPECAUDIT_ARCH.md
│   │   └── scan.py            the scan of the repository behind the proposal
│   ├── start/
│   │   ├── SKILL.md           /spec-audit:start, orchestrator: core protocol, phases 1 to 7, report
│   │   ├── references/
│   │   │   ├── launch.md      phase 0, steps 1 to 6: worktree, environment, audit session
│   │   │   ├── arch.py        reads SPECAUDIT_ARCH.md: roles, the check of each commit, the hook of the audit session
│   │   │   ├── report.md      template and rules of the final report
│   │   │   ├── corpus-errors.md  procedure for a guard suspected of being wrong
│   │   │   ├── closing.md     phase 8: closing, final commit, results folder, index, stop
│   │   │   ├── register.md    formats of the register, its entries, the guards, the index
│   │   │   ├── replay.py      replays a results folder's corpus on the original or the fixed document
│   │   │   └── with_docs.py   runs a command on another version of the document (SPEC_DOCS)
│   │   └── profiles/
│   │       └── formal.md      rules specific to formal documents
│   ├── stop/
│   │   └── SKILL.md           /spec-audit:stop, stops the audit running in the session
│   └── attest/
│       ├── SKILL.md           /spec-audit:attest, checks the signed tags of results folders
│       └── verify.py          the check itself, and the update of the index
├── agents/
│   ├── spec-reviewer.md       fresh reviewer, no history
│   └── spec-adjudicator.md    adjudicator: refute first, then confirm by execution
├── docs/                      installation, usage, how it works
├── examples/                  demo specification
├── evals/                     eval suite and end-to-end scripts (see evals/README.md)
├── mods/
│   └── specaudit-monitor/     optional plugin, experimental: the band and pane that follow an audit, and pause, stop or resume it
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE                    PolyForm Shield 1.0.0
```

## Future work, up for grabs

What is planned and not yet done. Each item is open to contributions: say in an issue which one you take, and see [CONTRIBUTING](CONTRIBUTING.md) for how changes are tested.

**Hypothesis discharge — high priority** ([design](docs/hypothesis-discharge.md)). Implemented; to validate on real documents of the `formal` profile, and to tune: which oracle level may mark an edge discharged, and a normalization of statements that lets a pure rewording keep its cache entries.

**Audit profiles** ([design](docs/profiles.md)). Step 1, the formal rules moved into `skills/start/profiles/formal.md`, is done, and step 3 is done in a more general form: `/spec-audit:init` proposes the profile of each document, with the rest of the project's architecture, and writes it into `SPECAUDIT_ARCH.md` once confirmed. Next:

| Step | What | Size |
|---|---|---|
| 2 | `profiles/functional.md` (ambiguous, incomplete, untestable or contradictory requirements; evidence by a replayed scenario, a decision table checked by script, or a contradiction quoted on both sides; acceptance tests as guards); agents made generic, the taxonomy passed in their message; `--profile <name>` | large: a profile, two agents, an eval fixture with planted defects and its graders |
| 3 | ~~a heuristic that proposes the profile from the document's signals, then writes the answer down~~: done by `/spec-audit:init`; left for step 2, the signals of the new profiles (`skills/init/scan.py`) | small |
| 4 | resources on demand: frozen sources exported with their SHA-256, executable oracles joining the allow list, normative references, each chosen by the user at phase 0 | medium |
| 5 | `research`, then `ui` and `experimental`, each tested on a real document of its domain | one profile at a time |

Open questions of the design: whether an argued contradiction may confirm an error alone or only escalate it; how frozen sources are refreshed between audits; whether one audit can mix documents of different profiles.

**Untested paths.** The stop and resume of an audit since the results folder exists (the stop needs an interactive session, which no test drives yet); Windows, where `plugin eval` cannot grant shell tools and only `evals/local-e2e.sh` runs; keyless signing with Sigstore's `gitsign` for attestation.

## Acknowledgments

A warm thank-you to [chteau](https://github.com/chteau), author of [tokenforge](https://github.com/chteau/tokenforge), for the idea that runs quietly under every long audit here: context is a budget, not a bin. Reducing what a session carries, and spending tokens on checking rather than on remembering, is what lets SpecAudit keep its reviewers cold and its audits long without drowning them in their own history.

## License

Copyright © 2026 Max Brönnimann. Starting with version 1.0.0-beta.6, SpecAudit is distributed under the [PolyForm Shield License 1.0.0](https://polyformproject.org/licenses/shield/1.0.0); see [LICENSE](LICENSE).

In plain language:

- you may use SpecAudit for any purpose, commercial included: auditing your own or your clients' documents, or using it as a consultant in paid engagements, and billing for the audits and the advice you deliver with it; the results of an audit are yours;
- you may change it, build on it and share it, as long as whoever gets a copy from you also gets the license terms (or their URL) and the `Required Notice:` line at the top of [LICENSE](LICENSE);
- the only thing you may not do is provide a product or service that competes with SpecAudit, or with a product its licensor provides using it: for example selling, renting, licensing or offering by subscription SpecAudit, an adapted version or a substitute for it. Under the license, a product competes even when it is free of charge or built on another platform.

This summary is for convenience only: it does not replace the text of the license, which alone is binding and prevails.

SpecAudit is provided **as is, without warranty** of any kind; see [Disclaimer](#disclaimer).

### License history

- **Initial experimental versions** (0.5 to 0.9.1): published for two days in October 2026 under the MIT License, in a former repository that has since been deleted.
- **Beta versions** (1.0.0-beta.1 up to the tag `v1.0.0-beta.5-cc`): CC BY-NC-SA 4.0, with additional permissions. A first 1.0.0-beta.1 had been published on 2026-10-11 under the EUPL-1.2 or the AGPL-3.0-or-later, before the history restarted at 1.0.0-beta.1 under CC BY-NC-SA 4.0.
- **From 1.0.0-beta.6**: PolyForm Shield 1.0.0.

Each version published before the change remains available under the license it was published with.
