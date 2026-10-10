# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [0.8.0] — 2026-10-10

### Changed

- Domain profiles, first step: the rules specific to formal documents (errors, form defects, inventory units, reviewer angles, oracles, evidence levels, guards, fixes of mapped statements, lint) move from `SKILL.md` to `skills/start/profiles/formal.md`, which the protocol refers to by section and the audit session receives with it. No change in behavior.

### Added

- Project configuration, tracked by git: `.specaudit.md`, or `.specaudit/` with `config.md`, normative references and project extensions of a profile. YAML front matter (profile per document pattern, normative dependencies, version convention, defaults of the options) and notes for the orchestrator; an option on the command wins over its defaults. The reviewers and the adjudicators never read it and receive only the normative files it declares. An untracked or ignored configuration triggers a warning and a question before the worktree is created: track it (recommended), use it for this audit only (SHA-256 recorded), or ignore it.
- `docs/profiles.md`: design of the audit profiles (functional, UI, research, experimental), their choice (`--profile`, `spec-audit/config.json`, heuristic confirmed at phase 0) and resources on demand (frozen sources, executable oracles, normative references).
- Corpus errors: a suspect guard (red on a fix considered valid, green on the original, flagged by the replay, red at the baseline) opens a `G-<iteration>-<n>` entry instead of being edited, and a fresh adjudicator in guard review judges it against the text, without the proposed fix: FAITHFUL (the regression rule applies), FAULTY (a new guard replaces it, red first, with any lost case listed), or UNDECIDED (escalated). The orchestrator writes both guards and fixes, so changing a guard on its own judgment would be judging its own work. Project tests are never changed, only reported. New eval cases `adjudicator-guard-review-faulty` and `-faithful`, and `e2e-faulty-guard-in-session`, a full audit of the demo as a previous audit left it, with a faulty guard red at the baseline: the audit must settle it as a corpus error and keep the correct Lemma 3 rather than bend it to the guard.
- Index `SPECAUDITS.md` at the root of the project: one row per results folder, newest first, with the audited source (a file or a folder), who launched it (git `user.name`; name and e-mail in the folder's README and the register, from the repository's git identity, else the system user, never guessed), launch time, base, outcome, closing answer, errors confirmed and fixed, and the fixed copy if any. Each closing adds its row and never rewrites the others; a merge conflict on the index alone is resolved by keeping both sides' rows. Reviewers and adjudicators never read it. `<document>` may now be a folder, which stands for the documents it contains, listed in the register.
- Text guards and replay: every error gets a text guard, which reads the document and fails on its original wording, since the other guards check an encoding of the statement and stay green if the text is reverted. Guards read the document through `SPEC_DOCS`, so the same corpus runs on the project and on either copy of a results folder. The folder ships `resources/replay.py` (from the plugin) and `resources/manifest.json`: `--on fixed` shows the fixes hold, `--on source` that each fixed error's text guard goes red on the original, and flags any error without one. When an error stays open, the partially fixed document is kept as `resources/<name>.partial<ext>`, out of the root. The README gets a "Tests" section, when test suites exist, with each suite's coverage, command and result at closing.
- Results folder: every audit run to completion, whatever its outcome and the answer at closing, leaves its whole result at the root of the project in `SpecAudit-YYYYmmdd_HHmm/`, named by the launch time of `/spec-audit:start` in local time (kept by `--resume`; `-2`, `-3`… if the name is taken, never overwritten): a README (outcome, identification of the sources with repository, branch and commits, table of contents, how to replay), the report and its annexes (details moved out when a section exceeds about ten entries), the register and the inventory; the fixed document(s) as `<name>.fixed<ext>`, only when every error could be fixed (no open error, no critical fix pending or refused, corpus and lint green), the README saying why otherwise; `source/`, the audited files as they were at the base; `docs/`, the documents consulted and a bibliography with what was checked; `resources/`, the corpus, `corrections.patch` and the executed counterexamples. Files that may hold credentials and files over 10 MB are referenced with their SHA-256, not copied, because the folder is committed and may be pushed. An interrupted audit (stop that cancels, execution error) keeps the dated archive under `spec-audit/<slug>/`. The register records the launch time (`Launched`), the remote of the original repository and the path of the results folder. Reviewers and adjudicators never read earlier results (`SpecAudit-*/`, `spec-audit/`).
- Report: each open point comes with its mitigation (what would settle it, the fix or hypothesis proposed, the check that would confirm it); an "Imprecisions" section lists correct but misleading passages with their clarification, fed by a new `misleading_wording` field of the adjudicator's REFUTED verdicts; and the report ends with a "Summary of issues", every issue sorted by priority (P1 claim false or unsupported now, P2 undecided or incomplete, P3 imprecisions and references, Done) with its mitigation and, when something supports it, an effort range in person-days with its basis and confidence, otherwise "not estimated".
- Eval suite in `evals/` (`claude plugin eval` format) and `evals/local-e2e.sh` for the audit-session mode, which plugin eval cannot cover.

### Fixed

- The skill names its own files from `${CLAUDE_SKILL_DIR}` (profile, register format) and the plugin's `agents/` and `docs/` from two levels up. With bare relative paths, the orchestrator could resolve `profiles/formal.md` against an inferred plugin root, have the read refused, and stop at phase 0.
- A counterexample is always executed: the adjudicator runs a script even for an obvious case, a confirmation evaluated by hand is UNDECIDED, and the orchestrator checks the script and its output before accepting a CONFIRMED verdict. The eval suite caught an adjudicator confirming at the ad hoc level with no script.
- Agents are named through their `description`, since the Agent tool has no name parameter, and the agent table records the id the launch returns, which is what `TaskStop` takes.
- An internal revision is committed only once the register holds the error's entry, its guards' red and green results, the agents involved and the revision's row: an audit session had fixed four errors with every table of its register still empty. Commits stage by path, so that test caches and bytecode stay out of the corpus.
- The oracle table records the exact command that was run and passed: an audit session failed its baseline on `python3 -m pytest` where only the `pytest` executable was installed.
- In the audit session, the agents could not execute anything: they had no Write tool and wrote their scripts through Bash heredocs, which the allow list (git and the oracle runners) refused, and the orchestrator ran the counterexamples in their place. The agents now have Write, limited by their instructions to their scratch directory, and run each script as one command, `<interpreter> <absolute path>`; the allow list adds that interpreter restricted to the scratch root, `Bash(python3 <worktree>-scratch/*)`. The orchestrator never runs a counterexample in an adjudicator's place: a refused execution makes the verdict UNDECIDED and is reported as an environment problem.
- A critical fix is judged on the statement being fixed, not on what depends on it: a lemma whose consequence is stated in the abstract is fixed as a cause, and the abstract's passage is the critical fix put to the user. Two runs of the demo had classified the Lemma 3 fix differently, one of them blocking the whole chain on an approval never asked for.
- The report never calls the document or a part of it "correct", only says what was checked and how, as it already did for "verified".
- Totals of the summary of issues add up the effort ranges per priority, instead of counting rows; the summary is the last section of the report, after a `Branch and closing` section that used to come last.
- Eval graders that passed on any run: the Lemma 3 fix (Definition 2 already contains `min(k, n)`) and "red first" (`red` matched "ignored"); `local-e2e.sh` no longer loses its revision check to SIGPIPE under `pipefail`.

## [0.7.0] — 2026-10-10

The audit now runs in a session of its own, and confirms errors on the project's own verification artifacts rather than on scripts it writes.

### Added

- Audit session: by default the orchestrator is a `claude -p` process launched by your session in the worktree, with no settings file (hence none of your plugins, hooks or connectors), no skill, no memory or conversation of yours, the two agents passed with `--agents`, and a Bash allow list that is exactly git (push denied) and the project's oracles. Your session prepares the worktree (phase 0, steps 1 to 6), waits, then runs the closing from the report and the register. `--in-session` keeps the former behavior.
- `--model <family|id>` and `--model-version <v>`: model of the audit session, passed to the `claude -p` process, which its agents inherit (default: the family of the launcher's model, `latest` version). The Opus requirement is gone.
- Environment, in phase 0: inventory of the session's resources the audit ignores, and **oracle table** of the project's verification artifacts (mechanized development, reference model or checker, test runner), each with its coverage and its command, run once in the worktree and ordered by strength. The table goes to every reviewer and every adjudicator; the register records it.
- Worktree autonomy: an ignored path an oracle needs is shared by a junction or symbolic link (third-party cache), copied with its SHA-256 recorded (unversioned input) or rebuilt (build output of the project); the baseline must be green from the worktree alone, otherwise the skill asks what to install or share. Once the audit has started, nothing is read in the original directory.
- Evidence levels on confirmations: formal (counterexample executed on the formal counterpart of the statement, through the document's correspondence table: `#eval`, `decide`, property-based search, or a refuting theorem), model, ad hoc. A statement with a formal counterpart confirmed only ad hoc stays UNDECIDED; the report counts confirmations by level. `Evidence` field in the register, `evidence` and `oracle` fields in the adjudicator's verdict, `oracle` field in the reviewer's errors.
- Safe interruption without pausing agents, which Claude Code cannot do:
  - "Questions only when idle": the orchestrator asks the user a question (escalated error, critical fixes, closing) only once no audit agent is running, since a question blocks it but not the background agents; the stop on request is the exception.
  - Replaceable agents: reviewers and adjudicators keep a `progress.md` (sections read or method step, candidate errors or verdict in progress, scripts and outputs) in their scratch directory, and reuse it if they find one, while redoing their judgment on the current text; a reviewer never takes over another agent's judgment.
  - Agent table in the register (name, role, error or wave, scratch directory, state `running` / `done` / `stopped` / `replaced by <name>`). A stopped or lost agent is never resumed with `SendMessage` (refused after a stop by the user, denied by tokenforge's lean mode): it is replaced by a fresh agent with the same message and scratch directory. `--resume` replaces every `running` or `stopped` agent before any other step; the stop report lists the interrupted agents and their scratch directories.
- Session history (tokenforge's `.forge/`, transcripts, handoffs): reviewers and adjudicators never read it. When git tracks such a folder, or with `--no-worktree`, phase 0 warns and asks before creating the worktree: untrack it and add it to `.gitignore` (recommended), or keep it ignored by the agents only; with `--no-worktree`, use a worktree (recommended) or continue. An untracked folder raises no question, since the worktree holds tracked files only.
- Guards in the oracle's language: for a formal oracle, a theorem or a decided check in a module the project's build compiles (Lean example in `references/register.md`); `native_decide` serves the search, never the recorded guard. The fix of a statement with a formal counterpart includes the formal statement, its proof and the correspondence table, in the same internal revision.

### Changed

- Agents declare `model: inherit` instead of `model: opus`: the model is a parameter of the command, not of the plugin.
- Roles: a Launcher (your session) joins the Orchestrator (the audit session, or you with `--in-session`). Phase 0 is renumbered: 4 Environment, 5 Register, 6 Audit session, 7 Inventory, 8 Baseline, 9 Lint.
- Stop (8.9) and `/spec-audit:stop`: in the default mode, the audit session's process is stopped first, which ends its agents; the rest of the stop is unchanged. A cleared conversation no longer means a stopped audit while that process is alive.
- The reviewers and the adjudicators may run the project's oracles named in their message, and must prefer them to their own scripts.

## [0.6.2] — 2026-10-10

### Changed

- Documentation brought in line with the published versions: README version badge, and the command rename moved from 0.6.0 to 0.6.1, the version that shipped it. No change in behavior.

## [0.6.1] — 2026-10-10

### Changed

- The audit command is now `/spec-audit:start` (skill folder `skills/start/`), paired with `/spec-audit:stop`; it was `/spec-audit:spec-audit`. In a manual installation, the folders are copied as `spec-audit-start` and `spec-audit-stop`.

## [0.6.0] — 2026-10-10

Closes a gap in the protocol: results that use a confirmed error without having been reported by a reviewer. Such a result is correct if the error is granted, so no reviewer flags it; until now it never entered the graph, and if the error stayed unfixed it was presented as correct.

### Added

- Suspects: as soon as an error is CONFIRMED, every result or passage that uses it directly (inventory and adjudicator's `impact`) enters the cause graph as a suspect, BLOCKED behind it, even if it is correct granting the error. The same applies to a consequence confirmed in 4.5, so propagation is transitive along confirmed links only.
- Suspect reassessment in 4.5: one fresh adjudicator can handle all the suspects of a cause, one verdict per suspect; REFUTED means the suspect holds and makes it RESOLVED. Suspects of an incomplete proof repaired without changing its statement are RESOLVED without adjudication.
- Register: `Origin` field on error entries (`reviewer (R…, wave …)` or `suspect (uses F-…)`) and `Suspects` column (added / cleared / confirmed) in the iteration log.
- Report: suspects counted apart from the errors; "Open points" lists the results conditional on an unresolved error (undecided, critical fix refused or pending, fix reverted), computed from the inventory, directly or through another result. An undecided error creates no suspects, since nothing in the text changes.
- A user decision on an escalated error counts as the adjudicator's verdict: judged false, the error becomes CONFIRMED and its suspects are marked.
- Internal revisions: each fixed error is committed in the worktree as revision r<N>, a verified state marked incomplete in its commit message and in the register (never in the document, which the reviewers read).
- `/spec-audit:stop` (`skills/stop`, user-invocable only) and phase 8.9: from the audit's session only, stops every audit agent (`TaskStop`, by the name given at launch), reports the last internal revision, marked incomplete, and asks whether to suspend, keep that revision as the new base (merged with the 8.5 checks) or cancel.
- Register header: session id (`${CLAUDE_SESSION_ID}`) and state (`running`, `stopping`, `suspended`, `closed`); table of internal revisions. The session is named `[AUDIT] <slug>` when the app allows it.
- `--resume` takes over an audit from another session only after the user confirms it no longer runs there, saves the unverified changes after the last revision as a patch and restarts from that revision.

### Changed

- Phase 3: a dependency without an edge no longer escapes rechecking: B can be both a root for its own error and a suspect behind A.
- 4.4 Propagation: rechecking the uses is required for every nature of fix (statement fix, scoping addition; a proof repair leaves them untouched), including uses without an edge.
- Suspects of a cause left unfixed (undecided, critical fix refused or pending, fix reverted after a regression) stay BLOCKED; the outcome is then "Partial, needs decision", never "Success".
- `spec-adjudicator` can receive suspects, and returns one verdict per suspect.

## [0.5.0] — 2026-10-09

First open-source release.

### Added

- `spec-audit` skill: iterative audit in a dedicated worktree, complete cold detection, triage by fingerprints, cause graph, bottom-up fixing, guards written and seen red before the fix, editorial track with a mechanical lint, seven stop conditions, final report and closing through a multiple-choice question.
- `spec-reviewer` agent: fresh reviewer with no history, returning errors and form defects in YAML.
- `spec-adjudicator` agent: adjudicator that tries to refute, then to confirm each error with an executed counterexample.
- `references/register.md` reference: formats of the register, of error and form defect entries, and of a guard file.
- `.claude-plugin/marketplace.json` marketplace: installation with `/plugin marketplace add magicmoux/SpecAudit`.
- Documentation: README, installation, usage, how it works, demo specification, contributing guide.
