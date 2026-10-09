# Utilisation

## Lancer un audit

Ouvrez Claude Code dans le dépôt git qui contient le document, puis invoquez le skill :

```text
/spec-audit:spec-audit <document> [options]
```

Avec une installation manuelle (sans plugin), la commande est `/spec-audit`.

Le skill se déclenche aussi sans être nommé, dès que vous demandez de relire, vérifier, auditer, durcir ou fiabiliser un document formel :

- « Vérifie les preuves de `theorie/chapitre-3.md`. »
- « Traque les erreurs dans les lemmes de `spec/protocole.md` avant soumission. »
- « Audite la spécification du format dans `docs/format.md`, trois itérations au plus. »

Précisez dans votre demande les **dépendances normatives** du document (les fichiers dont il utilise les définitions) : les relecteurs les recevront avec lui.

## Paramètres

| Paramètre | Défaut | Effet |
|---|---|---|
| `<document>` | — | le ou les fichiers audités |
| `--corpus <dossier>` | corpus de vérification existant du projet, sinon `spec-guards/` | où écrire les gardes ; les conventions du corpus existant (en-têtes, nommage, lanceur) sont respectées |
| `--max-iter N` | 5 | nombre maximal d'itérations détection → correction |
| `--auto` | non | applique aussi les corrections critiques (énoncé d'un résultat principal modifié, résultat retiré) sans attendre votre accord ; elles sont signalées dans le rapport |
| `--resume` | non | reprend un audit interrompu à partir de son registre, dans son worktree existant |
| `--base <réf>` | `HEAD` | branche ou commit de départ du worktree |
| `--no-worktree` | non | travaille dans le répertoire courant, quand il est déjà isolé pour l'audit |
| `--keep` | non | à la clôture, ne pose aucune question et conserve le worktree ; seul le rapport est rapatrié |

## Exemples

```text
# Audit d'un document, réglages par défaut
/spec-audit:spec-audit docs/specification.md

# Plusieurs fichiers, corpus de tests existant, budget réduit
/spec-audit:spec-audit theorie/definitions.md theorie/resultats.md --corpus tests/theorie --max-iter 3

# Partir d'une autre branche que la branche courante
/spec-audit:spec-audit spec/protocole.md --base develop

# Session sans surveillance : corrections critiques appliquées, worktree conservé à la fin
/spec-audit:spec-audit spec/format.md --auto --keep

# Reprendre un audit interrompu
/spec-audit:spec-audit spec/format.md --resume
```

## Déroulement, de votre point de vue

1. **Préparation.** Le skill lit les règles du projet (`CLAUDE.md`, conventions), qui priment sur les siennes. Il peut vous poser une question :
   - si le document, ses dépendances ou le corpus ont des modifications non commitées : elles n'existeront pas dans le worktree, faut-il auditer la version commitée ou commiter d'abord ?
   - si la convention de version du projet n'est pas claire : corriger en place, ou créer une nouvelle révision ?
   - si le dossier n'est pas un dépôt git : faut-il en initialiser un ?

   Il crée ensuite le worktree `<parent du dépôt>/<dépôt>-audit-<slug>` sur la branche `audit/<slug>`, où `<slug>` est le nom du document en minuscules.
2. **Itérations.** Détection, tri, graphe des causes, arbitrage, gardes, corrections et voie éditoriale s'enchaînent sans intervention. Le registre est tenu à jour après chaque étape.
3. **Corrections critiques.** Si une correction modifie l'énoncé d'un résultat principal ou retire un résultat, le skill traite d'abord le reste, puis vous présente ensemble les corrections critiques en attente (énoncé avant et après, contre-exemple, impact) et attend votre accord. Avec `--auto`, il les applique et le signale.
4. **Erreurs indécises.** Quand l'arbitre ne peut trancher, l'erreur vous est remontée sans modification du document, avec ce qui permettrait de décider ; ses conséquences restent bloquées.
5. **Clôture.** Le skill résume l'audit, donne le chemin du rapport complet et vous pose la question de clôture.

## Fichiers produits

Dans le worktree :

| Chemin | Contenu |
|---|---|
| le document | corrigé, selon la convention de version du projet |
| `spec-audit/<slug>/registre.md` | mémoire de l'audit : paramètres, journal des itérations, graphe des causes, entrées d'erreurs et de défauts de forme |
| `spec-audit/<slug>/inventaire.md` | chaque définition, lemme, proposition, théorème et algorithme, avec les résultats qu'il utilise |
| `spec-audit/<slug>/rapport.md` | rapport final |
| `<corpus>/` (`spec-guards/` par défaut) | gardes de chaque erreur et script de lint mécanique |

Les commits restent sur la branche `audit/<slug>`. Le skill ne commite que ses propres fichiers et ne pousse jamais.

Si vous choisissez « Conserver » ou « Abandonner », une archive est commitée dans la branche d'origine, sous `spec-audit/<slug>/<AAAA-MM-JJ>-<issue>/` : `rapport.md`, `registre.md` et `corrections.patch` (le diff complet de la branche d'audit, corrections et gardes comprises).

## Lire le rapport

| Section | Contenu |
|---|---|
| Résultat | motif d'arrêt, itérations, décompte des erreurs par statut, défauts de forme corrigés, commits |
| Graphe des causes | racines et chaînes de chaque itération, avec la justification de chaque arc ; un cycle éventuel en tête |
| Énoncés modifiés | pour chaque résultat touché : avant → après, nature de la correction, contre-exemple, gardes |
| Erreurs | tableau : identifiant, gravité, type, causes, statut, correction, gardes, commit |
| Points ouverts | erreurs indécises et chaînes bloquées, références à vérifier, récidives, oscillations, gardes modifiées, corrections critiques en attente, détection non saturée |
| Corpus | gardes et règles de lint ajoutées, commande pour tout rejouer |
| Portée de la vérification | ce qui a été vérifié et comment, et ce qui ne l'a pas été |

### Statuts des erreurs

| Statut | Sens |
|---|---|
| DÉTECTÉE | relevée par un relecteur, pas encore traitée |
| BLOQUÉE (par F-…) | conséquence d'une erreur pas encore corrigée : ni arbitrée, ni corrigée |
| CONFIRMÉE | l'arbitre l'a confirmée, preuve exécutée à l'appui |
| RÉFUTÉE | l'arbitre l'a écartée ; elle reste au registre pour écarter le même faux positif plus tard |
| INDÉCISE | l'arbitre n'a pas pu trancher ; aucune modification |
| ESCALADÉE | remontée à l'utilisateur, en attente de sa décision |
| CORRIGÉE | correction appliquée, gardes vertes |
| RÉSOLUE (par F-…) | disparue avec la correction de sa cause ; son cas rejoint les gardes de la cause |
| RÉCIDIVE | réapparition d'une erreur déjà corrigée : arrêt de l'audit |

## Clôture

L'issue de l'audit détermine l'option recommandée, toujours la plus sûre :

| Issue | Condition | Option recommandée |
|---|---|---|
| Succès | arrêt par convergence ou épuisement, corpus et lint verts, rien en attente | Accepter et fusionner |
| Partiel, à poursuivre | budget atteint ou détection non saturée, corpus et lint verts | Refaire une vérification |
| Partiel, à arbitrer | erreur indécise, chaîne bloquée ou correction critique en attente | Conserver le worktree |
| Échec | boucle causale, récidive, oscillation, non-convergence, corpus ou lint rouges, erreur d'exécution | Abandonner |

| Option | Effet |
|---|---|
| Accepter et fusionner | contrôles de sécurité, fusion `--no-ff` de `audit/<slug>` dans la branche d'origine, puis suppression du worktree et de la branche |
| Refaire une vérification | nouvelle série d'itérations dans le même worktree, avec de nouveaux agents et un nouveau budget ; rien n'est fusionné |
| Conserver le worktree | ni fusion ni suppression ; rapport, registre et patch archivés dans la branche d'origine |
| Abandonner | rapport, registre et patch archivés dans la branche d'origine, puis suppression du worktree et de la branche |

« Accepter » n'est jamais proposé si le corpus ou le lint sont rouges, et « Refaire » ne l'est pas après une boucle causale, une récidive, une oscillation ou une non-convergence. Une réponse libre ambiguë est reposée : le skill ne fusionne et ne supprime jamais sur une réponse ambiguë.

La fusion n'a pas lieu, et le worktree est conservé, si la branche d'origine a changé depuis le début de l'audit, si l'intégration de ses nouveaux commits provoque un conflit, si le corpus ou le lint repassent au rouge après cette intégration, ou si le dépôt d'origine a des modifications non commitées qui gênent la fusion.

## Après la clôture

- **Rejouer les gardes** : la commande figure dans la section « Corpus » du rapport.
- **Appliquer un patch archivé**, en tout ou partie :

  ```bash
  git apply --3way spec-audit/<slug>/<AAAA-MM-JJ>-<issue>/corrections.patch
  ```

- **Reprendre un worktree conservé** : relancez le skill avec `--resume`, ou demandez de rejouer seulement la clôture de l'audit.
- **Supprimer un worktree conservé** à la main :

  ```bash
  git worktree remove "<dépôt>-audit-<slug>"
  git branch -D audit/<slug>
  ```

- **Pousser** : le skill ne pousse jamais ; c'est à vous de le faire.

## Conseils

- **Commitez avant l'audit** : le worktree part de la version commitée.
- **Donnez un corpus existant** avec `--corpus` si le projet a déjà des tests de sa théorie : les gardes y seront écrites selon ses conventions et le lanceur du projet servira à les rejouer.
- **Bornez la dépense** avec `--max-iter` : chaque itération lance plusieurs agents Opus.
- **Documents longs** : le skill les découpe par sections, en donnant à chaque relecteur les définitions, la notation et la liste des énoncés, et ajoute une passe de cohérence entre sections.
- **Règles du projet** : ce que dit `CLAUDE.md` (attribution, versionnement des documents, politique de commit) prime sur le skill ; écrivez-y les contraintes propres à vos documents.
- **Bibliographie** : une référence n'est corrigée que contre sa source (PDF local, page de l'éditeur, DBLP) ; sinon elle est marquée « à vérifier ». Placez les sources dans le dépôt pour qu'elles puissent être consultées.
