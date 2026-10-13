# Installation

## Requirements

| Item | Why |
|---|---|
| Claude Code with plugin support (`/plugin`, `claude plugin`) | the skill and its agents ship as a plugin |
| git | the audit works in a dedicated worktree and commits locally there |
| A model for the agents | `spec-reviewer` and `spec-adjudicator` declare `model: inherit`: they run on the audit session's model, your session's by default, or the one given with `--model` and `--model-version` |
| An interpreter for the guards (Python 3 by default) | counterexamples and guards are executed scripts; the skill follows the project's test runner if it has one |
| A GPG or SSH signing key in git, or Sigstore's `gitsign` (optional) | to attest a result with a signed tag, on your own machine; `/spec-audit:attest` checks it |
| An interactive session (recommended) | critical fixes and closing go through a question to the user; without one, the worktree is kept and nothing is merged |

## 1. From the GitHub marketplace (recommended)

The repository is both the plugin and its own marketplace (`.claude-plugin/marketplace.json`), named `spec-audit`.

In Claude Code:

```text
/plugin marketplace add magicmoux/SpecAudit
/plugin install spec-audit@spec-audit
```

From the command line:

```bash
claude plugin marketplace add magicmoux/SpecAudit
claude plugin install spec-audit@spec-audit
```

### Installation scope

`claude plugin install` accepts `--scope`:

| Scope | Effect |
|---|---|
| `user` (default) | the plugin is available in all your projects |
| `project` | recorded in the project's `.claude/settings.json`, hence shared with the team through git |
| `local` | this project only, for you only (`.claude/settings.local.json`) |

```bash
claude plugin install spec-audit@spec-audit --scope project
```

## 2. For a team

To have the plugin offered to every member when they open the project, add to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "spec-audit": {
      "source": { "source": "github", "repo": "magicmoux/SpecAudit" }
    }
  },
  "enabledPlugins": {
    "spec-audit@spec-audit": true
  }
}
```

## 3. From a local clone

```bash
git clone https://github.com/magicmoux/SpecAudit.git
claude plugin marketplace add ./SpecAudit
claude plugin install spec-audit@spec-audit
```

To try a modified version without installing it, load it for a single session:

```bash
claude --plugin-dir ./SpecAudit
```

## 4. Without the plugin system

Copy the skill and the agents into your user configuration.

Bash:

```bash
mkdir -p ~/.claude/skills ~/.claude/agents
cp -r SpecAudit/skills/start ~/.claude/skills/spec-audit-start
cp -r SpecAudit/skills/init ~/.claude/skills/spec-audit-init
cp -r SpecAudit/skills/stop ~/.claude/skills/spec-audit-stop
cp -r SpecAudit/skills/attest ~/.claude/skills/spec-audit-attest
cp SpecAudit/agents/*.md ~/.claude/agents/
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills", "$HOME\.claude\agents" | Out-Null
Copy-Item -Recurse SpecAudit\skills\start "$HOME\.claude\skills\spec-audit-start"
Copy-Item -Recurse SpecAudit\skills\init "$HOME\.claude\skills\spec-audit-init"
Copy-Item -Recurse SpecAudit\skills\stop "$HOME\.claude\skills\spec-audit-stop"
Copy-Item -Recurse SpecAudit\skills\attest "$HOME\.claude\skills\spec-audit-attest"
Copy-Item SpecAudit\agents\*.md "$HOME\.claude\agents\"
```

For a single project, copy them into `.claude/skills/` and `.claude/agents/` at the project root instead. Keep the folder names given above: the stop skill finds the start skill's `references/closing.md` in `../spec-audit-start/`, the init skill its `references/arch.py` there too, and each skill copies its `references/` and scripts with it.

The names change: a skill takes the name of its folder, so the commands are `/spec-audit-init`, `/spec-audit-start`, `/spec-audit-stop` and `/spec-audit-attest`, and the agents `spec-reviewer` and `spec-adjudicator` (instead of `/spec-audit:init`, `/spec-audit:start`, `/spec-audit:stop`, `/spec-audit:attest`, `spec-audit:spec-reviewer` and `spec-audit:spec-adjudicator`). The skill recognizes both forms of the agent names.

## Check the installation

```bash
claude plugin list
claude plugin details spec-audit
```

The plugin must appear as `spec-audit@spec-audit`, with four skills (`init`, `start`, `stop`, `attest`) and two agents. In a session, `/agents` lists `spec-audit:spec-reviewer` and `spec-audit:spec-adjudicator`, and typing `/spec-audit` suggests `/spec-audit:init`, `/spec-audit:start`, `/spec-audit:stop` and `/spec-audit:attest`.

## Update

```bash
claude plugin marketplace update spec-audit
claude plugin update spec-audit@spec-audit
```

The new version is loaded in the next session. Changes are described in the [changelog](../CHANGELOG.md).

## Uninstall

```bash
claude plugin uninstall spec-audit@spec-audit
claude plugin marketplace remove spec-audit
```

For a manual installation, delete `~/.claude/skills/spec-audit-init/`, `~/.claude/skills/spec-audit-start/`, `~/.claude/skills/spec-audit-stop/`, `~/.claude/skills/spec-audit-attest/`, `~/.claude/agents/spec-reviewer.md` and `~/.claude/agents/spec-adjudicator.md`.

Audits already carried out are not affected: their reports, registers and guards stay in your repositories.

## Troubleshooting

| Symptom | Cause and remedy |
|---|---|
| The agents appear twice (`spec-reviewer` and `spec-audit:spec-reviewer`) | a manual installation coexists with the plugin: delete the manual copies (previous section) |
| `Filename too long` when cloning on Windows | enable long paths: `git config --global core.longpaths true` |
| `marketplace add` fails with an authentication error | the repository is not public or git has no access to it: sign in (`gh auth login`) or use a local clone |
| The skill does not trigger on a natural-language request | invoke it explicitly: `/spec-audit:start <document>` |
| The agents cannot be found | the skill then launches a fresh general-purpose agent with the content of `agents/spec-reviewer.md` or `agents/spec-adjudicator.md` as instructions; check the installation anyway, since the dedicated agents restrict the allowed tools |
| With `--in-session` and tokenforge's lean mode, `TaskStop` and `SendMessage` are denied | the stop asks you to stop the agents yourself with `/tasks` (or the desktop app's tasks pane); the resume still works, since interrupted agents are replaced by fresh ones, never resumed with `SendMessage`. The default mode is not affected: the audit session loads none of your settings |
| The audit stops at the baseline: an oracle's command does not run (`No module named pytest`, command not found) | the oracle table records the command exactly as it ran at phase 0, and the audit session may run nothing else; install the runner where the worktree can reach it, or record the form that works (`pytest` and `python3 -m pytest` are not interchangeable), then `--resume` |
| `git tag -s` in a cloud session signs with a key that is not yours | such environments may replace git's signing program with their own: attest on your own machine, after `git fetch` (see `/spec-audit:attest`) |
| A model is not available to you | choose another one with `--model` (family alias or full id) and `--model-version` (default `latest`); the agents inherit it |
