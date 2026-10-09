# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [0.5.0] — 2026-10-09

First open-source release.

### Added

- `spec-audit` skill: iterative audit in a dedicated worktree, complete cold detection, triage by fingerprints, cause graph, bottom-up fixing, guards written and seen red before the fix, editorial track with a mechanical lint, seven stop conditions, final report and closing through a multiple-choice question.
- `spec-reviewer` agent: fresh reviewer with no history, returning errors and form defects in YAML.
- `spec-adjudicator` agent: adjudicator that tries to refute, then to confirm each error with an executed counterexample.
- `references/register.md` reference: formats of the register, of error and form defect entries, and of a guard file.
- `.claude-plugin/marketplace.json` marketplace: installation with `/plugin marketplace add magicmoux/SpecAudit`.
- Documentation: README, installation, usage, how it works, demo specification, contributing guide.
