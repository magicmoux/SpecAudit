# SpecAudit-20261011_075706 — audit of `bubble-sort.md`

**Outcome: Partial, needs decision.** Stop reason: budget (`--max-iter 1`). A critical fix (Algorithm 7 does not sort; F-1-3 / F-1-4) is pending approval. Note: one lint check (`test_cross_references_resolve`, the dangling "Corollary 8", D-1-1) is red on purpose until that fix is approved, so the corpus is not fully green (25 passed, 1 failed).

- Launched by: SpecAudit demo <demo@example.invalid> (git, cloud session), 2026-10-11 07:57:06 UTC+0000; model of the audit session: sonnet (latest)
- Closing: `--keep` given, so "Keep the worktree" (question not asked). Nothing merged.
- Sources: original repository `<repo>` (no remote), branch `master`, base `c58def9`; audit branch `audit/bubble-sort` at `25a8670` (worktree `<repo>-audit-bubble-sort`).
- Fixed document: **not at the root**: a critical fix is pending. The head of the branch is in `resources/bubble-sort.partial.md`; every fix is in `resources/corrections.patch`.
- Detection was not saturated for convergence: a second clean detection after the pending fix is required.

## Attestation
Not attested. After reading the report, the person who stands by the result signs a tag on their own machine: `git tag -s specaudit/SpecAudit-20261011_075706 "$(git log -1 --format=%H -- SpecAudit-20261011_075706)" -m "Attest SpecAudit-20261011_075706: …"`, then `/spec-audit:attest` checks it. "Launched by" is not an attestation and the audit never signs.

## Contents
- [report.md](report.md): final report
- [register.md](register.md), [inventory.md](inventory.md): annexes
- [source/bubble-sort.md](source/bubble-sort.md): the document as at the base commit
- docs/: none (no normative or bibliographic documents; the document has no bibliography)
- [resources/corpus/](resources/corpus/): guard corpus and lint (`test_F_1_3.py` guards the pending fix and is left out of the manifest)
- [resources/manifest.json](resources/manifest.json), [resources/replay.py](resources/replay.py): replay
- [resources/corrections.patch](resources/corrections.patch): all fixes and guards; replay with `git apply --3way resources/corrections.patch`
- [resources/counterexamples/](resources/counterexamples/): the executed script of each confirmed error (outputs were recorded in the register, not as files)
- [resources/bubble-sort.partial.md](resources/bubble-sort.partial.md): head of the audit branch

## Tests
Corpus (pytest, from this folder): `python3 resources/replay.py --on fixed` → 6 of 7 guards green; the lint is red as explained above (D-1-1). `--on source` → each fixed error's text guard and the lint red, the statement guards green (7/7 as expected). In the project: `pytest -q -p no:cacheprovider spec-guards` in the worktree, last result 25 passed, 1 failed.
