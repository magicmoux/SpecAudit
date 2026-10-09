# Contribuer

Les contributions sont les bienvenues : signalements, corrections, améliorations du protocole ou de la documentation.

## Signaler un problème

Ouvrez une [issue](https://github.com/magicmoux/SpecAudit/issues) en indiquant :

- la version de Claude Code (`claude --version`) et celle du plugin (`claude plugin list`) ;
- le type de document audité, sans contenu confidentiel ;
- la phase concernée et l'extrait utile du registre ou du rapport ;
- le comportement attendu et le comportement observé.

Un faux positif confirmé, une correction qui renforce un énoncé, un relecteur qui a reçu de l'historique ou un worktree perdu sont des bugs du protocole : ils sont prioritaires.

## Structure

| Fichier | Rôle |
|---|---|
| `.claude-plugin/plugin.json` | manifeste du plugin : nom, version, métadonnées |
| `.claude-plugin/marketplace.json` | le dépôt est sa propre marketplace |
| `skills/spec-audit/SKILL.md` | consignes de l'orchestrateur, phases 0 à 8 |
| `skills/spec-audit/references/registre.md` | formats du registre, des entrées et des gardes, chargés à la demande |
| `agents/spec-reviewer.md` | consignes et format de sortie du relecteur |
| `agents/spec-adjudicator.md` | consignes et format de sortie de l'arbitre |
| `docs/` | documentation utilisateur |
| `examples/` | spécification de démonstration à erreurs connues |

## Développer en local

```bash
git clone https://github.com/magicmoux/SpecAudit.git
cd SpecAudit
claude --plugin-dir .
```

`--plugin-dir` charge le plugin pour la session sans l'installer. Relancez la session après chaque modification du skill ou des agents.

Si vous avez aussi installé le plugin depuis la marketplace, ou copié le skill dans `~/.claude/`, désactivez ces copies pendant le développement pour ne pas tester la mauvaise version.

## Valider

```bash
claude plugin validate --strict .
```

La commande vérifie les manifestes et les en-têtes du skill et des agents. Elle doit passer sans avertissement.

## Tester une modification

Il n'y a pas de tests automatiques du comportement d'un skill : testez sur la [spécification de démonstration](examples/), avant et après votre modification, et comparez les registres et les rapports. Vérifiez au moins :

- que les relecteurs ne reçoivent ni registre, ni corpus, ni erreurs précédentes, et qu'aucun agent n'est lancé en « fork » ;
- que chaque garde est vue rouge avant la correction ;
- que les erreurs attendues sont trouvées, corrigées de bas en haut, sans sur-correction de la Proposition 4 ;
- que la clôture recommande l'option prévue pour l'issue obtenue et rapatrie le rapport.

Pour une modification du protocole, testez aussi sur un document réel du domaine visé et décrivez le résultat dans la pull request.

## Conventions

- **Langue** : le skill, les agents et la documentation sont en français ; le README garde un résumé en anglais.
- **Style des consignes** : expliquez pourquoi une règle existe plutôt que de l'imposer ; un modèle qui comprend la raison généralise mieux qu'un modèle qui obéit.
- **Cohérence** : les types d'erreur, les statuts, les gravités et les formats YAML sont partagés entre `SKILL.md`, les deux agents et `references/registre.md`. Modifiez-les ensemble, et mettez à jour la documentation.
- **Version** : versionnage sémantique dans `.claude-plugin/plugin.json` (correctif : comportement inchangé ; mineure : nouvelle capacité compatible ; majeure : protocole, formats ou paramètres incompatibles), avec une entrée dans `CHANGELOG.md`. Après fusion, `claude plugin tag .` crée l'étiquette `spec-audit--v<version>`.

## Pull requests

1. Créez une branche depuis `main`.
2. Une pull request par sujet, avec la description du changement de comportement attendu.
3. Mettez à jour la documentation et le journal des modifications.
4. Vérifiez que `claude plugin validate --strict .` passe.

## Licence

En contribuant, vous acceptez que votre contribution soit publiée sous [licence MIT](LICENSE).
