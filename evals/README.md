# Eval suite

Behavioral tests of the plugin, in the `claude plugin eval` format: each case is a folder with a `case.yaml` (prompt, limits, graders) and, for most, a `scaffold.sh` that builds the workspace from the test specification `_fixtures/selection.md` (incremental selection of the k smallest elements, with planted errors; the demo for readers, `examples/demo/bubble-sort.md`, is built the same way).

They test what a reader of the protocol cannot check by reading it: that the agents keep their independence, that an executed counterexample backs each confirmation, that a full audit leaves the files and the results folder it promises, and that the audit does not bend a correct statement to fit a test.

## Cases

| Case | Tags | What it checks |
|---|---|---|
| `start-skill-triggers` | quick | a request to check the proofs of a formal document loads the start skill |
| `stop-without-audit` | quick | `/spec-audit:stop` with no audit running says so and changes nothing |
| `reviewer-finds-planted-errors` | quick | a fresh reviewer finds the planted errors and does not flag the correct Proposition 4 |
| `reviewer-ignores-session-history` | quick | a reviewer is not steered by a handoff, the audit configuration, the index of audits (`SPECAUDITS.md`, a lure that says Lemma 3 was found correct and other results need no review) or the results folder of an earlier audit; it may read `SPECAUDIT_ARCH.md` |
| `start-refuses-without-arch` | quick | `/spec-audit:start` in a repository without `SPECAUDIT_ARCH.md` refuses, names `/spec-audit:init`, and launches and writes nothing |
| `init-proposes-architecture` | shell | `/spec-audit:init`, where no question can be asked, on `_fixtures/arch-project/`: each path its expected role, the Lean oracle its command, correspondence table and guard location, the mapped pair; nothing written or committed |
| `adjudicator-refutes-false-positive` | quick | an adjudicator refutes a false claim against Proposition 4 instead of forcing a confirmation |
| `adjudicator-confirms-with-counterexample` | shell | an adjudicator confirms Lemma 3 with a counterexample it actually ran |
| `adjudicator-probe-lifts-counterexample` | shell | in probe mode, an adjudicator finds that Proposition 3 of `_fixtures/squares.md` applies Lemma 2 without guaranteeing its hypothesis, with a counterexample run under Proposition 3's hypotheses, and lifts it to Theorem 4 |
| `adjudicator-guard-review-faulty` | shell | in guard review, an adjudicator finds faulty a guard whose model drops duplicates |
| `adjudicator-guard-review-faulty-low`, `-faithful-low` | measure | the same two guard reviews at `low` effort: the measurement behind running guard reviews at `low` (`--runs 3` to re-measure) |
| `adjudicator-guard-review-faithful` | shell | in guard review, an adjudicator finds a correct guard faithful, rather than faulting every guard |
| `attest-never-signs` | shell | `/spec-audit:attest` reports an unsigned folder as not attested and gives the command to sign it, without signing anything |
| `attest-does-not-guess` | shell | with no argument and two folders to attest, `/spec-audit:attest` lists both instead of picking one |
| `agents-pass-preflight` | shell | an adjudicator given the preflight probe runs it in the scratch directory given and answers in the checked format, without judging anything |
| `e2e-demo-in-session` | e2e, shell | full audit of the demo: register, inventory, report with its summary of issues, Lemma 3 fixed, Proposition 4 unchanged, guards red first, results folder recorded |
| `e2e-faulty-guard-in-session` | e2e, shell | full audit of the demo as a previous audit left it, with a faulty guard red at the baseline: a corpus error is opened, a fresh adjudicator reviews the guard, it is replaced, and Lemma 3 is not bent to fit it |

`quick` cases run in a minute or two each. `shell` cases grant Bash and need the sandbox; `e2e` cases run a whole audit (up to 200 turns, an hour at most, about $1 each).

## Running

**Which account pays.** Every case and every local script launches `claude`, billed to the account the claude CLI is logged into (`claude auth status`), whatever the session that starts them. The local scripts refuse to start unless `SPECAUDIT_E2E_ACCOUNT` names that account's e-mail (`_fixtures/account-guard.sh`). Started from the Claude desktop app, a script would otherwise inherit the app's credentials, which win over `CLAUDE_CONFIG_DIR`: the guard removes them first (`account.py clean-env`). `claude plugin eval` has no such guard: from the desktop app, run it under `env $(python skills/start/references/account.py clean-env) CLAUDE_CONFIG_DIR=…`. They also cap their spending: at most `SPECAUDIT_E2E_MARGIN` points (default 1, or `session=1,week=2` for each window) of usage above what the account used when the batch started, in its session window and in its week. The ceiling is computed once per session window by a tiny request, shared by every script started before that window resets, and passed to each audit as `--pause-at` with `--no-auto-resume`, so that an audit past it pauses and its test ends; `SPECAUDIT_E2E_CEILING="session=N,week=N"` sets it instead. To run them, or `claude plugin eval`, on another account, log it in once under its own configuration folder, then pass that folder each time:

```bash
CLAUDE_CONFIG_DIR="$HOME/.claude-perso" claude auth login
CLAUDE_CONFIG_DIR="$HOME/.claude-perso" SPECAUDIT_E2E_ACCOUNT=<its e-mail> evals/local-e2e.sh audit-session sonnet
```

Run the tier that covers what you changed, and the whole suite before a pull request:

| Tier | Command (from the repository root) | Time | When |
|---|---|---|---|
| quick | `claude plugin eval . --tag quick …`, and `evals/arch.sh` | 1 to 2 min | any change to the agents or the protocol |
| agents, attest | `--tag agents --tag attest` | about 3 min | a change to an agent, the preflight or `/spec-audit:attest` |
| e2e | `--tag e2e`, then `evals/local-e2e.sh audit-session` | about 10 min | a change to the protocol, before a merge |
| full | no tag, then `arch.sh`, `account.sh`, `local-init.sh`, `journal.sh`, `local-e2e.sh`, `local-e2e-no-merge.sh`, `local-e2e-folder.sh`, `local-e2e-discharge.sh`, `local-e2e-fail-fast.sh`, `local-e2e-pause.sh` and `local-e2e-kill.sh` | about 10 min at `-j 6` | before a pull request |
| parallel | `local-e2e-parallel.sh` | about 10 min | a change to the index (`SPECAUDITS.md`, `index.py`), the launch or the closing: two audits launched at the same moment are rare, so this run, about $1.60, is not part of the suite before every pull request |
| measure | `--tag measure --runs 3` | about 2 min | to re-measure what justifies a lowered effort |

Where `…` stands for the options below. The two e2e cases set the wall-clock time; at `-j 6` the others run alongside them. More concurrency than that mostly makes the runs wait on the same account's rate limit, since every run uses the same credential.

The whole suite:

```bash
claude plugin eval . --scaffold --allow-tools Bash Agent Skill Write Edit --ablation none --trust-plugin --no-publish -j 6 --json evals/results/all.json
```

- `--scaffold` runs the cases' `scaffold.sh`, which only build a demo repository in the case's temporary workspace.
- `--case <glob>` runs one case; the flag keeps only its last value, so run several cases by tag (`--tag quick`) or one command per case.
- `--keep-temp` keeps each workspace, to read the register and the report an audit wrote; the run's transcript is in its `out/trace.jsonl`.
- Results and an HTML report go to `evals/results/`, which git ignores.

**Shell cases need a sandbox.** `plugin eval` refuses to grant Bash without one rather than run it unconfined. On Linux, install `bubblewrap` and `socat` (`apt install bubblewrap socat`); on Windows, where there is no sandbox backend, only the cases without Bash run, and `local-e2e.sh` below covers the full audit.

## The audit session: `local-e2e.sh`

`plugin eval` runs a case in the session it starts, so it cannot cover the default mode, where the audit runs in a `claude -p` session of its own in a worktree. `local-e2e.sh` runs that mode on the demo, as you, in a throwaway repository under the temp directory, and checks the result on disk: register, guards red first, agent table, internal revisions, no two agents overlapping (from the journals the hooks keep in each scratch directory), every agent and every verdict tied to a commit of the audit's branch, the branch named `audit/<stamp>` with the results folder's stamp and ending with a final commit, nothing merged into the original branch (no merge commit, the document untouched, only the results folder and `SPECAUDITS.md` committed there, both naming the branch and its final commit), the results folder `SpecAudit-<YYYYmmdd_HHmmss>/` (README, unfixed `source/`, executed counterexamples, no runner cache), both replays of the corpus, a report with the template's sections in order and the summary of issues last, a `## Consumption` section whose total is the one `consumption.py` measures on the run's streams (with `in-session`: a section saying it was not measured), and a report that never claims the document is correct.

```bash
evals/local-e2e.sh audit-session sonnet                         # one iteration: a critical fix stays pending
evals/local-e2e.sh audit-session sonnet "--auto --max-passes 2"   # everything fixed: the fixed copy is expected at the root
evals/local-e2e.sh in-session sonnet                            # the in-session mode, outside plugin eval
```

The third argument replaces the default audit options, `--max-passes 1`.

`evals/local-e2e-parallel.sh` launches two audits at the same moment from the same repository, on two documents with opposite scenarios: `selection.md` without `--auto` (a critical fix stays pending, no fixed copy) and `_fixtures/sums.md` with `--auto` (its false proposition fixed, its true lemma kept, a fixed copy). It checks that they share nothing (branches `audit/<stamp>`, worktrees, launch files, scratch roots, results folders), that each runs its agents one at a time, that neither is merged, that both closings land in the original repository (two index entries, no leftover git lock, documents untouched), each verdict, and that each report's consumption is measured from its own audit session's streams. Each run costs about $0.50 and leaves its repository for inspection; the path is printed at the end.

Two more scripts cover what neither of the above reaches, at about $0.60 each:

- `evals/local-e2e-no-merge.sh`: the closing without `--keep`, with `--auto` and two passes, so that every error can be fixed. A `claude -p` session cannot ask the closing question, so the audit applies "Keep the branch"; the script checks that it never merges: the branch `audit/<stamp>` kept with its final commit, no merge commit and no fix on the original branch, the original document untouched, the results folder and the index entry back on the original branch naming the branch and its final commit, a report that proposes no merge, and the corpus green on the fixed copy.
- `evals/local-e2e-kill.sh`: an agent killed in the middle of its work, with the audit session, then `--resume`: the hooks kept its prompt and its journal without a result, and the resume replaced it with the same prompt in the same scratch directory, up to the report.
- `evals/local-e2e-pause.sh`: a pause on a usage threshold (`--pause-at 1 --no-auto-resume`): the pause request, the register suspended for the usage limit, every launched agent's prompt kept; then `--resume`, which does not run again the agents that have a result, and carries the audit to its report.
- `evals/local-e2e-fail-fast.sh`: `--fail-fast` on the demo: a stop on a confirmed root error (Lemma 3 or Example 6, never their consequence Corollary 5), the document unchanged, no fix committed, and a report whose "First error" section gives the proposed fix and the results the error may affect.
- `evals/local-e2e-discharge.sh`: hypothesis discharge on `examples/discharge/block-search.md`: the use edges recorded, a red probe on Proposition 3 → Lemma 2 with the error put on Proposition 3, Theorem 6 added by lifting, Lemma 2 and Proposition 4 unchanged, and the probes cached and committed in the corpus.
- `evals/local-e2e-folder.sh`: a folder as the target, `docs/` holding `selection.md` and `sums.md`, with `--auto`: one audit for both documents, each fixed as its own errors require, the index naming the folder, and the results folder holding each original and each fixed copy, with the replay red on the originals and green on the fixed copies.

## Architecture: `arch.sh` and `local-init.sh`

Every repository the cases and scripts build has a `SPECAUDIT_ARCH.md`, written by `_fixtures/write-arch.sh` (each document given `audited`, `formal`), since `/spec-audit:start` refuses to run without one.

`evals/arch.sh` tests the two scripts behind the architecture, without a model, in a second: `skills/init/scan.py` on `_fixtures/arch-project/` (an original manuscript and hard-to-find references in `source/`, the revised version and proofs in `artifacts/`, a Lean development with a correspondence table in `mechanization/`; Lean need not be installed) gives each path its expected role, the oracle, the guard location and the mapped pair, and on the demo marks `selection.md` alone as audited; `skills/start/references/arch.py` refuses an audit without the file (exit 2, naming `/spec-audit:init`) and with an invalid one, refuses a commit that touches a read-only path (the original, a reference, the oracle's build file, a path not listed, the architecture, a counterpart changed without its document), and, as the audit session's hook, refuses such an edit and an agent's read of the index, a results folder, the register, the configuration or the original, while letting it read `SPECAUDIT_ARCH.md`; it also reads the configuration's deprecated keys, and shows a role changed by hand against init's proposal.

`evals/local-init.sh` runs the two skills for real, non-interactively, for a few cents: `/spec-audit:init` on the fixture project prints the expected proposal and writes and commits nothing; `/spec-audit:start` on the demo without the file refuses and leaves no worktree, register, index entry or commit.

## Attestation: `attest-verify.sh`

`evals/attest-verify.sh` tests `skills/attest/verify.py` on real signed tags, with a throwaway SSH key and repository: one folder per status (valid, unsigned, changed after signing, key not trusted, tampered tag, no tag), the resolution of a target (stamp, path, audited source, unknown target, folders still to attest) and the `--update` of the index. It needs git and `ssh-keygen`, no model and no network, and runs in a second.

## The hook: `journal.sh`

`evals/journal.sh` tests `skills/start/references/journal.py` on synthetic hook events: every launch forced to the foreground, a second launch refused while the first agent has not returned (and nothing left in its scratch directory), the lock released when the Agent call returns or fails, a stale lock taken over once its agent has its result, a launch refused by a pause not holding the lock, a deleted launcher session (`--launcher`) stopping the audit with its own state, and no change without `--lock`; and `_fixtures/serial_check.py`, which the end-to-end scripts run on an audit's journals to tell whether two agents overlapped. No model, no network; it runs in a second.

## The launcher's account: `account.sh`

`evals/account.sh` tests `account.py check` on simulated accounts: configuration folders under a throwaway home, each with a `fake-auth.json` standing for `claude auth status` there. The check passes only while the folder the register records is logged in to the e-mail it records, the e-mail compared without case; it refuses a folder logged in to another account (the `claude auth login` of someone else while the audit waits), logged out or gone, and names the other folders logged in to the recorded e-mail; the desktop app's own account does not decide; and `check --session` compares an `--in-session` audit's account with the session's, exit 3 when that is unknown. No model, no network, no real login read; it runs in a second.

## Consumption: `consumption.sh`

`evals/consumption.sh` tests `skills/start/references/consumption.py` on two synthetic streams, `_fixtures/stream-sample.jsonl` and `_fixtures/stream-sample-resume.jsonl`, placed as the launch folder holds them after one `--resume`: the orchestrator and two agents named from their scratch directories, one assistant message repeated on two lines and counted once, the total taken from the last `result` event of each run, the agents' output from their transcripts or left unattributed without them, shares summing to 100, cost per model and in total with none per agent, the windows' shares with a reset during the second run, and the section put in place of the report's placeholder. No model, no network; it runs in a second.

## Writing a case

- Prefer graders that read files or the transcript (`file_exists`, `regex`, `tool_used`) to LLM judges; when a judge is needed, state the criterion so that any notation passes ("the minimum of k and the length of L, in any notation") rather than one spelling.
- Anchor a regex on the statement it is about: Definition 2 already contains `min(k, n)`, so an unanchored pattern for the fix of Lemma 3 passes on the untouched document.
- A name that depends on the time (the results folder) cannot be a `file_exists` path: grade the path the register records.
- Pair a case that expects a fault with one that expects none (`guard-review-faulty` and `-faithful`), so that an agent that always finds fault does not pass.
