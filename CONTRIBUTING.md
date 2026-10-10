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
| `skills/spec-audit/SKILL.md` | orchestrator instructions, phases 0 to 8 |
| `skills/spec-audit/references/register.md` | formats of the register, its entries and the guards, loaded on demand |
| `skills/stop/SKILL.md` | `/spec-audit:stop`, user-only entry point that stops the audit running in the session |
| `agents/spec-reviewer.md` | reviewer instructions and output format |
| `agents/spec-adjudicator.md` | adjudicator instructions and output format |
| `docs/` | user documentation |
| `examples/` | demo specification with known errors |

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

There are no automated tests of a skill's behavior: test on the [demo specification](examples/), before and after your change, and compare the registers and the reports. Check at least:

- that the reviewers receive no register, no corpus and no previous errors, and that no agent is launched as a "fork";
- that each guard is seen red before the fix;
- that the expected errors are found and fixed bottom-up, without over-correcting Proposition 4;
- that the closing recommends the option expected for the outcome obtained and brings the report back.

For a change to the protocol, also test on a real document of the target domain and describe the result in the pull request.

## Conventions

- **Language**: the skill, the agents and the documentation are written in English.
- **Instruction style**: explain why a rule exists rather than imposing it; a model that understands the reason generalizes better than a model that obeys.
- **Consistency**: error types, statuses, severities and YAML formats are shared between `SKILL.md`, the two agents and `references/register.md`. Change them together, and update the documentation.
- **Version**: semantic versioning in `.claude-plugin/plugin.json` (patch: unchanged behavior; minor: new compatible capability; major: incompatible protocol, formats or parameters), with an entry in `CHANGELOG.md`. After merging, `claude plugin tag .` creates the tag `spec-audit--v<version>`.

## Pull requests

1. Create a branch from `main`.
2. One pull request per topic, describing the expected change in behavior.
3. Update the documentation and the changelog.
4. Check that `claude plugin validate --strict .` passes.

## License

By contributing, you agree that your contribution is published under the [MIT license](LICENSE).
