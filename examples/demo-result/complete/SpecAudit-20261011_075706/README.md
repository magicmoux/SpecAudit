# SpecAudit-20261011_075706

**Outcome**: Partial, to continue. Stop reason: budget (`--max-iter 2` reached). Five errors confirmed and all fixed; convergence not established, because the final text had no fresh cold detection after the last fixes.

- **Audited**: `bubble-sort.md`
- **Launched by**: SpecAudit demo <demo@example.invalid> (git identity, cloud session; not an attestation), 2026-10-11 07:57:06 UTC+0000. Closed 2026-10-11.
- **Closing**: "Keep the worktree", applied because of `--keep`; no question was asked.
- **Model of the audit session**: sonnet (latest)
- **Sources**: repository `<repo>` (no remote), branch `master`, base `c58def9`; head of `audit/bubble-sort` at closing `282a779`; no merge.
- **Fixed document**: [bubble-sort.fixed.md](bubble-sort.fixed.md), at the root because every confirmed error is FIXED or RESOLVED and the corpus and lint are green. Detection was saturated in both iterations, but not re-run on the final text. The fixes change what the document claims: the "faster variant" now shortens passes at the end instead of starting them later, and the Abstract and Conclusion changed with it (critical fix applied under `--auto`). Read them first.
- **Attestation**: Not attested. After reading the report, the person who stands by the result signs a tag on their own machine: `git tag -s specaudit/SpecAudit-20261011_075706 "$(git log -1 --format=%H -- SpecAudit-20261011_075706)" -m "Attest SpecAudit-20261011_075706: ..."`, then `/spec-audit:attest` checks it. The "Launched by" identity is not an attestation and the audit never signs.

## Contents

- [report.md](report.md): the final report
- [bubble-sort.fixed.md](bubble-sort.fixed.md): the fixed document
- [register.md](register.md): the register (annex)
- [inventory.md](inventory.md): the inventory (annex)
- [source/bubble-sort.md](source/bubble-sort.md): the document as it was at the base
- [docs/bibliography.md](docs/bibliography.md): the document has no references
- [resources/corpus/](resources/corpus/): the guard corpus and lint
- [resources/replay.py](resources/replay.py), [resources/manifest.json](resources/manifest.json): replay of the checks
- [resources/corrections.patch](resources/corrections.patch): every fix and guard
- [resources/counterexamples/](resources/counterexamples/): the scripts that executed the confirmed errors (the outputs were not kept in the scratch directories)

## Replay

`git apply --3way resources/corrections.patch`

## Tests

The audit's corpus, 29 tests (10 files), covers statements, text guards and the lint. No project suite exists. From this folder:

- `python3 resources/replay.py --on fixed`: every guard green (last result: 10/10).
- `python3 resources/replay.py --on source`: the text guard of each fixed error and the lint red, the other guards green (last result: 10/10).

In the worktree: `pytest -q -p no:cacheprovider spec-guards`, 29 passed at closing.
