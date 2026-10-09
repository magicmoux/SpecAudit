# SpecAudit

**Plugin Claude Code d'audit itératif de précision pour les spécifications théoriques, techniques ou mathématiques.**

[![Licence MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)
![Version 0.5.0](https://img.shields.io/badge/version-0.5.0-informational.svg)
![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A63D2.svg)

> **In English.** SpecAudit is a Claude Code plugin that audits formal documents — papers, proofs, algorithm, protocol or format specifications — for logical, mathematical and algorithmic errors. Fresh reviewer agents with no history detect the errors; an independent adjudicator agent confirms each one with an executed counterexample; confirmed errors are ordered into a cause graph and fixed bottom-up, each fix being preceded by a regression guard in a growing test corpus. The whole audit runs in a dedicated git worktree and ends with a report and a multiple-choice closing question (merge, re-check, keep, abandon). The skill, the agents and the reports are written in French; the audited documents can be in any language.

## Pourquoi

Un auteur ne voit plus ses propres angles morts, et un relecteur qui connaît l'historique lit ce qu'il s'attend à lire. `spec-audit` sépare donc les rôles : des relecteurs neufs qui ne savent rien de l'audit, un arbitre qui confirme ou réfute chaque erreur, et un orchestrateur qui tient le registre, classe les erreurs, écrit les gardes et corrige.

Trois principes guident le reste :

- **Une erreur non confirmée n'est pas une erreur.** Les relecteurs produisent des faux positifs, et corriger un énoncé juste abîme le document autant que laisser un énoncé faux.
- **On corrige une cause avant ses conséquences.** Corriger d'abord une conséquence masque la cause, ou la compense au mauvais endroit.
- **Une erreur corrigée sans garde reviendra.** Chaque correction laisse dans le corpus un test qui échouerait si l'erreur réapparaissait.

## Fonctionnalités

- **Détection à froid** : des agents `spec-reviewer` neufs, sans historique ni registre, relisent tout le document par vagues jusqu'à ce qu'une vague n'apporte plus rien.
- **Confirmation par l'exécution** : un agent `spec-adjudicator` neuf cherche d'abord à réfuter chaque erreur, puis à la confirmer par un contre-exemple minimal exécuté.
- **Graphe des causes** : les erreurs sont classées en chaînes de causalité et corrigées de bas en haut ; une conséquence reste bloquée tant que sa cause n'est pas corrigée, et une boucle causale arrête l'audit.
- **Gardes anti-régression** : garde témoin écrite et vue rouge avant la correction, variantes aux cas limites, quasi-cas contre la sur-correction, vérification bornée, gardes de classe pour les énoncés frères.
- **Corrections minimales et tracées** : correctif d'énoncé, complément de cadrage ou réparation de preuve ; jamais de renforcement, jamais de suppression silencieuse ; les corrections critiques attendent votre accord.
- **Voie éditoriale séparée** : typos, numérotation, renvois et bibliographie, avec un lint mécanique qui grandit à chaque classe de défaut corrigée.
- **Isolation git** : tout se passe dans un worktree `audit/<slug>`, avec des commits locaux, sans toucher à votre répertoire de travail et sans jamais pousser.
- **Arrêt explicite** : convergence, budget, récidive, oscillation, non-convergence, boucle causale ou épuisement.
- **Clôture décidée par vous** : rapport complet, puis question à choix multiple (accepter et fusionner, refaire une vérification, conserver, abandonner), l'option la plus sûre étant recommandée.

## Installation

Dans Claude Code :

```text
/plugin marketplace add magicmoux/SpecAudit
/plugin install spec-audit@spec-audit
```

Ou en ligne de commande :

```bash
claude plugin marketplace add magicmoux/SpecAudit
claude plugin install spec-audit@spec-audit
```

Installation pour un projet ou une équipe, depuis un clone local, ou sans système de plugins : voir [docs/installation.md](docs/installation.md).

## Démarrage rapide

Depuis le dépôt git qui contient le document :

```text
/spec-audit:spec-audit docs/specification.md
```

Le skill se déclenche aussi en langage naturel, par exemple : « Vérifie les preuves de `docs/specification.md` avant soumission. »

Pour voir un audit complet sans risque, lancez-le sur la spécification de démonstration de [examples/](examples/), qui contient des erreurs connues.

## Paramètres

| Paramètre | Effet |
|---|---|
| `<document>` | le ou les fichiers audités |
| `--corpus <dossier>` | corpus global de gardes (défaut : le corpus de vérification du projet, sinon `spec-guards/`) |
| `--max-iter N` | nombre maximal d'itérations (défaut : 5) |
| `--auto` | appliquer aussi les corrections critiques sans attendre votre accord |
| `--resume` | reprendre un audit interrompu dans son worktree |
| `--base <réf>` | branche ou commit de départ du worktree (défaut : `HEAD`) |
| `--no-worktree` | travailler sur place, sans worktree |
| `--keep` | ne poser aucune question à la clôture et conserver le worktree |

Détails et exemples : [docs/utilisation.md](docs/utilisation.md).

## Ce que produit un audit

Dans le worktree `<dépôt>-audit-<slug>`, sur la branche `audit/<slug>` :

- le document corrigé, une correction par erreur confirmée, commitée localement ;
- `spec-audit/<slug>/registre.md` : la mémoire de l'audit (journal, graphe des causes, chaque erreur avec son contre-exemple, son verdict, ses gardes et sa correction) ;
- `spec-audit/<slug>/inventaire.md` : définitions, résultats et leurs dépendances ;
- `spec-audit/<slug>/rapport.md` : le rapport final ;
- le corpus de gardes et le script de lint, rejouables à tout moment.

Quelle que soit l'issue, le rapport revient dans la session et dans la branche d'origine ; si vous ne fusionnez pas, un `corrections.patch` y est archivé avec lui.

## Prérequis

- Claude Code avec la prise en charge des plugins ;
- git (le document doit se trouver dans un dépôt, sinon le skill propose d'en initialiser un) ;
- l'accès au modèle Opus, que déclarent les deux agents ;
- un interpréteur pour exécuter contre-exemples et gardes : Python 3 par défaut, ou le lanceur de tests du projet.

Un audit lance plusieurs agents par itération : il consomme beaucoup de jetons. `--max-iter` borne la dépense.

## Ce que l'audit ne garantit pas

Une relecture par des agents et des tests bornés ne sont ni une relecture par les pairs ni une preuve. L'audit ne conclut jamais « le document est correct », mais « N détections indépendantes n'ont plus relevé d'erreur confirmée », en disant ce qui n'a pas été vérifié. Seule une preuve mécanisée peut être dite vérifiée par machine.

## Documentation

- [Installation](docs/installation.md) : modes d'installation, vérification, mise à jour, désinstallation, dépannage.
- [Utilisation](docs/utilisation.md) : lancement, paramètres, déroulement, fichiers produits, clôture, reprise.
- [Fonctionnement](docs/fonctionnement.md) : rôles, phases, graphe des causes, gardes, conditions d'arrêt.
- [Exemple](examples/) : spécification de démonstration à erreurs connues.
- [Journal des modifications](CHANGELOG.md) et [guide de contribution](CONTRIBUTING.md).

## Contenu du dépôt

```text
SpecAudit/
├── .claude-plugin/
│   ├── plugin.json            manifeste du plugin
│   └── marketplace.json       le dépôt sert aussi de marketplace
├── skills/spec-audit/
│   ├── SKILL.md               orchestrateur : phases 0 à 8
│   └── references/
│       └── registre.md        formats du registre, des entrées et des gardes
├── agents/
│   ├── spec-reviewer.md       relecteur neuf, sans historique
│   └── spec-adjudicator.md    arbitre : réfuter d'abord, puis confirmer par l'exécution
├── docs/                      installation, utilisation, fonctionnement
├── examples/                  spécification de démonstration
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

## Licence

[MIT](LICENSE).
