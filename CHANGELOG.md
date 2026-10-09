# Journal des modifications

Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et les versions suivent le [versionnage sémantique](https://semver.org/lang/fr/).

## [0.5.0] — 2026-10-09

Première publication open source.

### Ajouté

- Skill `spec-audit` : audit itératif en worktree dédié, détection complète à froid, tri par empreintes, graphe des causes, correction de bas en haut, gardes écrites rouges avant la correction, voie éditoriale avec lint mécanique, sept conditions d'arrêt, rapport final et clôture par question à choix multiple.
- Agent `spec-reviewer` : relecteur neuf, sans historique, qui rend erreurs et défauts de forme au format YAML.
- Agent `spec-adjudicator` : arbitre qui cherche à réfuter puis à confirmer chaque erreur par un contre-exemple exécuté.
- Référence `references/registre.md` : formats du registre, des entrées d'erreur et de défaut, et d'un fichier de garde.
- Marketplace `.claude-plugin/marketplace.json` : installation par `/plugin marketplace add magicmoux/SpecAudit`.
- Documentation : README, installation, utilisation, fonctionnement, spécification de démonstration, guide de contribution.
