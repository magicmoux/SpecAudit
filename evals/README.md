# Eval suite

Behavioral tests of the plugin, in the `claude plugin eval` format: each case is a folder with a `case.yaml` (prompt, limits, graders) and, for most, a `scaffold.sh` that builds the workspace from the demo specification (`_fixtures/selection.md`, the same document as `examples/demo/`).

They test what a reader of the protocol cannot check by reading it: that the agents keep their independence, that an executed counterexample backs each confirmation, that a full audit leaves the files and the results folder it promises, and that the audit does not bend a correct statement to fit a test.

## Cases

| Case | Tags | What it checks |
|---|---|---|
| `start-skill-triggers` | quick | a request to check the proofs of a formal document loads the start skill |
| `stop-without-audit` | quick | `/spec-audit:stop` with no audit running says so and changes nothing |
| `reviewer-finds-planted-errors` | quick | a fresh reviewer finds the planted errors and does not flag the correct Proposition 4 |
| `reviewer-ignores-session-history` | quick | a reviewer is not steered by a handoff, the audit configuration or the results folder of an earlier audit |
| `adjudicator-refutes-false-positive` | quick | an adjudicator refutes a false claim against Proposition 4 instead of forcing a confirmation |
| `adjudicator-confirms-with-counterexample` | shell | an adjudicator confirms Lemma 3 with a counterexample it actually ran |
| `adjudicator-guard-review-faulty` | shell | in guard review, an adjudicator finds faulty a guard whose model drops duplicates |
| `adjudicator-guard-review-faithful` | shell | in guard review, an adjudicator finds a correct guard faithful, rather than faulting every guard |
| `attest-never-signs` | shell | `/spec-audit:attest` reports an unsigned folder as not attested and gives the command to sign it, without signing anything |
| `e2e-demo-in-session` | e2e, shell | full audit of the demo: register, inventory, report with its summary of issues, Lemma 3 fixed, Proposition 4 unchanged, guards red first, results folder recorded |
| `e2e-faulty-guard-in-session` | e2e, shell | full audit of the demo as a previous audit left it, with a faulty guard red at the baseline: a corpus error is opened, a fresh adjudicator reviews the guard, it is replaced, and Lemma 3 is not bent to fit it |

`quick` cases run in a minute or two each. `shell` cases grant Bash and need the sandbox; `e2e` cases run a whole audit (up to 200 turns, an hour at most, about $1 each).

## Running

From the repository root:

```bash
claude plugin eval . --scaffold --allow-tools Bash Agent Skill Write Edit --ablation none --trust-plugin --no-publish -j 3 --json evals/results/all.json
```

- `--scaffold` runs the cases' `scaffold.sh`, which only build a demo repository in the case's temporary workspace.
- `--case <glob>` runs one case; the flag keeps only its last value, so run several cases by tag (`--tag quick`) or one command per case.
- `--keep-temp` keeps each workspace, to read the register and the report an audit wrote; the run's transcript is in its `out/trace.jsonl`.
- Results and an HTML report go to `evals/results/`, which git ignores.

**Shell cases need a sandbox.** `plugin eval` refuses to grant Bash without one rather than run it unconfined. On Linux, install `bubblewrap` and `socat` (`apt install bubblewrap socat`); on Windows, where there is no sandbox backend, only the cases without Bash run, and `local-e2e.sh` below covers the full audit.

## The audit session: `local-e2e.sh`

`plugin eval` runs a case in the session it starts, so it cannot cover the default mode, where the audit runs in a `claude -p` session of its own in a worktree. `local-e2e.sh` runs that mode on the demo, as you, in a throwaway repository under the temp directory, and checks the result on disk: register, guards red first, agent table, internal revisions, the results folder `SpecAudit-<YYYYmmdd_HHmm>/` (README, unfixed `source/`, executed counterexamples, no runner cache), both replays of the corpus, and a report that never claims the document is correct.

```bash
evals/local-e2e.sh audit-session sonnet                         # one iteration: a critical fix stays pending
evals/local-e2e.sh audit-session sonnet "--auto --max-iter 2"   # everything fixed: the fixed copy is expected at the root
evals/local-e2e.sh in-session sonnet                            # the in-session mode, outside plugin eval
```

The third argument replaces the default audit options, `--max-iter 1`. Each run costs about $0.50 and leaves its repository for inspection; the path is printed at the end.

## Attestation: `attest-verify.sh`

`evals/attest-verify.sh` tests `skills/attest/verify.py` on real signed tags, with a throwaway SSH key and repository: one folder per status (valid, unsigned, changed after signing, key not trusted, tampered tag, no tag) and the `--update` of the index. It needs git and `ssh-keygen`, no model and no network, and runs in a second.

## Writing a case

- Prefer graders that read files or the transcript (`file_exists`, `regex`, `tool_used`) to LLM judges; when a judge is needed, state the criterion so that any notation passes ("the minimum of k and the length of L, in any notation") rather than one spelling.
- Anchor a regex on the statement it is about: Definition 2 already contains `min(k, n)`, so an unanchored pattern for the fix of Lemma 3 passes on the untouched document.
- A name that depends on the time (the results folder) cannot be a `file_exists` path: grade the path the register records.
- Pair a case that expects a fault with one that expects none (`guard-review-faulty` and `-faithful`), so that an agent that always finds fault does not pass.
