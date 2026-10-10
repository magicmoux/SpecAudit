# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

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

- The audit command is now `/spec-audit:start` (skill folder `skills/start/`), paired with `/spec-audit:stop`; it was `/spec-audit:spec-audit`. In a manual installation, the folders are copied as `spec-audit-start` and `spec-audit-stop`.

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
