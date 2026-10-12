# SpecAudit index

Every audit launched in this project, newest first. Each entry is written at launch and updated when the audit ends, however it ends; an entry still RUNNING whose audit is no longer running was interrupted without a chance to say so (`--resume` or `/spec-audit:stop` updates it).

| Date | Audited object | Launched by | Result |
|---|---|---|---|
| [2026-10-11 07:57:06](#specaudit-20261011_075706) | `bubble-sort.md` | SpecAudit demo | FINISHED — Partial, to continue |

## SpecAudit-20261011_075706

Audit of `bubble-sort.md`, launched by SpecAudit demo from a cloud session on `master`. It confirmed five errors and fixed all of them, each with guards: Lemma 3 and Corollary 5 were false, Algorithm 7 did not sort, and the Abstract and Conclusion described the wrong variant. The "faster variant" is now a different algorithm from the one originally written, and the Abstract and Conclusion edits were applied under `--auto`, so read them first. The two-iteration budget ended the audit before a final fresh review of the fixed text. The worktree was kept (`audit/bubble-sort`); a further iteration can be run with `--resume`.

| | |
|---|---|
| Launched | 2026-10-11 07:57:06 UTC+0000, by SpecAudit demo <demo@example.invalid> (git, cloud session) |
| Audited object | `bubble-sort.md` |
| Base | `c58def9` on `master` |
| Result | FINISHED — Partial, to continue |
| Closing | Keep the worktree |
| Errors confirmed / fixed | 5 / 5 |
| Fixed copy | yes (`bubble-sort.fixed.md`) |
| Results folder | [SpecAudit-20261011_075706/](SpecAudit-20261011_075706/README.md) |
| Attested | no |
