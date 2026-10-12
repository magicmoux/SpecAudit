# SpecAudit index

Every audit launched in this project, newest first. Each entry is written at launch and updated when the audit ends, however it ends; an entry still RUNNING whose audit is no longer running was interrupted without a chance to say so (`--resume` or `/spec-audit:stop` updates it).

| Date | Audited object | Launched by | Result |
|---|---|---|---|
| [2026-10-11 07:57:06](#specaudit-20261011_075706) | `bubble-sort.md` | SpecAudit demo | FINISHED — Partial, needs decision |

## SpecAudit-20261011_075706

Audit of `bubble-sort.md`, launched by SpecAudit demo from a cloud session on `master`. It confirmed five errors and fixed three (Lemma 3, Corollary 5, Example 6) with guards. Algorithm 7 does not sort ((3,2,1) returns (2,1,3)); its fix changes what the abstract and conclusion claim, so it awaits approval, and convergence was not established in one iteration. The worktree was kept.

| | |
|---|---|
| Launched | 2026-10-11 07:57:06 UTC+0000, by SpecAudit demo <demo@example.invalid> (git, cloud session) |
| Audited object | `bubble-sort.md` |
| Base | `c58def9` on `master` |
| Result | FINISHED — Partial, needs decision |
| Closing | Keep the worktree |
| Errors confirmed / fixed | 5 / 3 |
| Fixed copy | no (a critical fix is pending) |
| Results folder | [SpecAudit-20261011_075706/](SpecAudit-20261011_075706/README.md) |
| Attested | no |
