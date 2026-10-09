# Installation

## Prérequis

| Élément | Pourquoi |
|---|---|
| Claude Code avec la prise en charge des plugins (`/plugin`, `claude plugin`) | le skill et ses agents sont livrés en plugin |
| git | l'audit travaille dans un worktree dédié et y commite localement |
| Accès au modèle Opus | les agents `spec-reviewer` et `spec-adjudicator` déclarent `model: opus` |
| Un interpréteur pour les gardes (Python 3 par défaut) | contre-exemples et gardes sont des scripts exécutés ; le skill suit le lanceur de tests du projet s'il en a un |
| Une session interactive (recommandé) | les corrections critiques et la clôture passent par une question à l'utilisateur ; sans elle, le worktree est conservé et rien n'est fusionné |

## 1. Depuis la marketplace GitHub (recommandé)

Le dépôt est à la fois le plugin et sa propre marketplace (`.claude-plugin/marketplace.json`), nommée `spec-audit`.

Dans Claude Code :

```text
/plugin marketplace add magicmoux/SpecAudit
/plugin install spec-audit@spec-audit
```

En ligne de commande :

```bash
claude plugin marketplace add magicmoux/SpecAudit
claude plugin install spec-audit@spec-audit
```

### Portée de l'installation

`claude plugin install` accepte `--scope` :

| Portée | Effet |
|---|---|
| `user` (défaut) | le plugin est disponible dans tous vos projets |
| `project` | inscrit dans `.claude/settings.json` du projet, donc partagé par git avec l'équipe |
| `local` | ce projet seulement, pour vous seul (`.claude/settings.local.json`) |

```bash
claude plugin install spec-audit@spec-audit --scope project
```

## 2. Pour une équipe

Pour que chaque membre se voie proposer le plugin en ouvrant le projet, ajoutez à `.claude/settings.json` :

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

## 3. Depuis un clone local

```bash
git clone https://github.com/magicmoux/SpecAudit.git
claude plugin marketplace add ./SpecAudit
claude plugin install spec-audit@spec-audit
```

Pour essayer une version modifiée sans l'installer, chargez-la pour une seule session :

```bash
claude --plugin-dir ./SpecAudit
```

## 4. Sans système de plugins

Copiez le skill et les agents dans votre configuration utilisateur.

Bash :

```bash
mkdir -p ~/.claude/skills ~/.claude/agents
cp -r SpecAudit/skills/spec-audit ~/.claude/skills/
cp SpecAudit/agents/*.md ~/.claude/agents/
```

PowerShell :

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills", "$HOME\.claude\agents" | Out-Null
Copy-Item -Recurse SpecAudit\skills\spec-audit "$HOME\.claude\skills\"
Copy-Item SpecAudit\agents\*.md "$HOME\.claude\agents\"
```

Pour un seul projet, copiez-les plutôt dans `.claude/skills/` et `.claude/agents/` à la racine du projet.

Les noms changent : le skill s'appelle `/spec-audit`, les agents `spec-reviewer` et `spec-adjudicator` (au lieu de `/spec-audit:spec-audit`, `spec-audit:spec-reviewer` et `spec-audit:spec-adjudicator`). Le skill reconnaît les deux formes.

## Vérifier l'installation

```bash
claude plugin list
claude plugin details spec-audit
```

Le plugin doit apparaître comme `spec-audit@spec-audit`, avec un skill et deux agents. Dans une session, `/agents` liste `spec-audit:spec-reviewer` et `spec-audit:spec-adjudicator`, et la saisie de `/spec-audit` propose `/spec-audit:spec-audit`.

## Mettre à jour

```bash
claude plugin marketplace update spec-audit
claude plugin update spec-audit@spec-audit
```

La nouvelle version est chargée à la session suivante. Les changements sont décrits dans le [journal des modifications](../CHANGELOG.md).

## Désinstaller

```bash
claude plugin uninstall spec-audit@spec-audit
claude plugin marketplace remove spec-audit
```

Pour une installation manuelle, supprimez `~/.claude/skills/spec-audit/`, `~/.claude/agents/spec-reviewer.md` et `~/.claude/agents/spec-adjudicator.md`.

Les audits déjà menés ne sont pas touchés : leurs rapports, registres et gardes restent dans vos dépôts.

## Dépannage

| Symptôme | Cause et remède |
|---|---|
| Les agents apparaissent deux fois (`spec-reviewer` et `spec-audit:spec-reviewer`) | une installation manuelle coexiste avec le plugin : supprimez les copies manuelles (section précédente) |
| `Filename too long` en clonant sous Windows | activez les chemins longs : `git config --global core.longpaths true` |
| `marketplace add` échoue avec une erreur d'authentification | le dépôt n'est pas public ou git n'a pas d'accès : connectez-vous (`gh auth login`) ou utilisez un clone local |
| Le skill ne se déclenche pas sur une demande en langage naturel | invoquez-le explicitement : `/spec-audit:spec-audit <document>` |
| Les agents sont introuvables | le skill lance alors un agent généraliste neuf avec le contenu de `agents/spec-reviewer.md` ou `agents/spec-adjudicator.md` comme consigne ; vérifiez tout de même l'installation, car les agents dédiés limitent les outils autorisés |
| Le modèle Opus n'est pas disponible | le modèle est fixé par l'en-tête des agents : installez depuis un clone local (section 3) et modifiez `model:` dans `agents/*.md` |
