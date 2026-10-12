# Contributing

Contributions are welcome: bug reports, fixes, improvements to the protocol or the documentation.

## Reporting an issue

Open an [issue](https://github.com/magicmoux/SpecAudit/issues) stating:

- the Claude Code version (`claude --version`) and the plugin version (`claude plugin list`);
- the type of document audited, without confidential content;
- the phase concerned and the relevant excerpt of the register or the report;
- the expected behavior and the observed behavior.

A confirmed false positive, a fix that strengthens a statement, a reviewer that received history, or a lost worktree are protocol bugs: they take priority.

## Layout

| File | Role |
|---|---|
| `.claude-plugin/plugin.json` | plugin manifest: name, version, metadata |
| `.claude-plugin/marketplace.json` | the repository is its own marketplace |
| `skills/start/SKILL.md` | `/spec-audit:start`, orchestrator instructions: principles, roles, phases 0 (steps 7 to 9) to 7, report |
| `skills/start/references/launch.md`, `report.md`, `corpus-errors.md`, `closing.md` | phase 0 steps 1 to 6, the report template, the procedure for a suspect guard, and phase 8 with the stop: each read when it comes; the audit session never loads the launch and the closing |
| `skills/start/references/register.md` | formats of the register, its entries and the guards, loaded on demand |
| `skills/start/profiles/*.md` | domain profiles: errors, evidence, guards, oracles, lint (`formal` today; design in `docs/profiles.md`) |
| `skills/attest/SKILL.md`, `skills/attest/verify.py` | `/spec-audit:attest`, user-only: checks the signed tags `specaudit/<folder>` and records them in the index; never signs |
| `skills/stop/SKILL.md` | `/spec-audit:stop`, user-only entry point that stops the audit running in the session |
| `agents/spec-reviewer.md` | reviewer instructions and output format |
| `agents/spec-adjudicator.md` | adjudicator instructions and output format |
| `docs/` | user documentation |
| `examples/` | demo specification with known errors |
| `evals/` | eval suite (`claude plugin eval`) and `local-e2e.sh` for the audit session; see `evals/README.md` |
| `skills/start/references/replay.py` | replay of a results folder's corpus on the original or the fixed document, copied into each folder |

## Developing locally

```bash
git clone https://github.com/magicmoux/SpecAudit.git
cd SpecAudit
claude --plugin-dir .
```

`--plugin-dir` loads the plugin for the session without installing it. Restart the session after each change to the skill or the agents.

If you have also installed the plugin from the marketplace, or copied the skill into `~/.claude/`, disable those copies while developing so as not to test the wrong version.

## Validating

```bash
claude plugin validate --strict .
```

The command checks the manifests and the frontmatter of the skill and the agents. It must pass without warnings.

## Testing a change

Run the eval suite before and after your change ([`evals/README.md`](evals/README.md)): the tier that covers your change (the table there says which), and the whole suite with the local end-to-end scripts before a pull request (`local-e2e-parallel.sh` only for a change to the index, the launch or the closing). A change that fixes a behavior adds a case that would have failed before it.

The suite does not cover everything; on the [demo specification](examples/), also compare the registers and the reports before and after, and check at least:

- that the reviewers receive no register, no corpus and no previous errors, and that no agent is launched as a "fork";
- that each guard is seen red before the fix;
- that the expected errors are found and fixed bottom-up, without over-correcting Proposition 4;
- that the closing recommends the option expected for the outcome obtained and brings the report back.

For a change to the protocol, also test on a real document of the target domain and describe the result in the pull request.

## Conventions

- **Language**: the skill, the agents and the documentation are written in English.
- **Instruction style**: explain why a rule exists rather than imposing it; a model that understands the reason generalizes better than a model that obeys.
- **Context economy**: every word of `SKILL.md` stays in the context of every audit session for the whole audit. Say a rule once, where it applies; put what only one moment needs (launch, closing) in `references/`, read when it comes; and hand each agent only what its step needs.
- **Consistency**: error types, statuses, severities and YAML formats are shared between `skills/start/SKILL.md`, its `references/` (`launch.md`, `closing.md`, `register.md`), `skills/stop/SKILL.md`, `skills/attest/`, the two agents and the profiles. Every profile has the same sections, which the protocol names; change them together, and update the documentation.
- **Version**: semantic versioning in `.claude-plugin/plugin.json` (patch: unchanged behavior; minor: new compatible capability; major: incompatible protocol, formats or parameters), with an entry in `CHANGELOG.md`. After merging, `claude plugin tag .` creates the tag `spec-audit--v<version>`.

## Pull requests

1. Create a branch from `main`.
2. One pull request per topic, describing the expected change in behavior.
3. Update the documentation and the changelog.
4. Check that `claude plugin validate --strict .` passes.

## License and contributor agreement

SpecAudit is licensed under CC BY-NC-SA 4.0, with the additional permissions in [LICENSE](LICENSE). By opening a pull request, you agree to the following:

1. Your contribution is your own work, or you have the right to submit it, and it is published under the license of the project, CC BY-NC-SA 4.0 with the additional permissions in LICENSE. Material taken from another project may be contributed only if its license allows this, and its license and origin are stated in the pull request.
2. You keep the copyright on your contribution, and may use it as you wish elsewhere.

State it in the pull request with the line `I agree to the contributor agreement in CONTRIBUTING.md.`
