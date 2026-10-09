---
name: spec-audit
description: >-
  Audit itératif de précision d'une spécification théorique, technique ou mathématique
  (manuscrit, article, preuve, spécification d'algorithme, de protocole ou de format),
  mené dans un worktree git dédié : détection complète à froid par des agents neufs sans historique, classement des erreurs
  en chaînes de causalité, correction des causes avant leurs conséquences (de bas en haut),
  confirmation de chaque erreur par un contre-exemple exécuté, gardes anti-régression dans
  un corpus global de tests, correction des énoncés, du cadrage et des preuves, puis des
  typos, de la bibliographie, de la numérotation et des renvois, et nouvelle passe jusqu'à
  convergence, épuisement du budget, récidive d'une erreur corrigée ou boucle causale.
  Clôture par une question à choix multiple à l'utilisateur (accepter et fusionner, refaire
  une vérification, conserver, abandonner), l'option la plus sûre étant recommandée, et
  rapport rapatrié dans la session et la branche d'origine dans tous les cas.
  À utiliser dès que l'utilisateur veut relire, vérifier, auditer, durcir ou fiabiliser un
  document formel, traquer des erreurs dans des théorèmes, lemmes, algorithmes ou preuves,
  ou préparer une spécification avant soumission ou publication, même sans dire « audit ».
argument-hint: "<document> [--corpus <dossier>] [--max-iter N] [--auto] [--resume] [--base <réf>] [--no-worktree] [--keep]"
---

# Audit de précision d'une spécification

Un auteur ne voit pas ses propres angles morts, et un relecteur qui connaît l'historique lit ce qu'il s'attend à lire. Ce skill sépare donc les rôles : des relecteurs neufs qui ne savent rien de l'audit, un arbitre qui confirme ou réfute chaque erreur, et toi, l'orchestrateur, qui tiens le registre, classes les erreurs, écris les gardes et corriges. Trois principes guident tout le reste :

- **Une erreur non confirmée n'est pas une erreur.** Les relecteurs produisent des faux positifs, et corriger un énoncé juste abîme le document autant que laisser un énoncé faux.
- **On corrige une cause avant ses conséquences.** Corriger d'abord une conséquence masque la cause, ou la compense localement (une hypothèse ajoutée au mauvais endroit).
- **Une erreur corrigée sans garde reviendra.** Chaque correction laisse dans le corpus un test qui échouerait si l'erreur réapparaissait.

## Ce qui compte comme erreur

Une **erreur** est un défaut du contenu propre au domaine du document (logique, mathématique, algorithmique, théorique) :

- un énoncé faux (un contre-exemple existe) ;
- une preuve invalide ou lacunaire ;
- un cadrage insuffisant : hypothèse manquante, contexte ou domaine d'application non restreint, cas limite non traité ;
- une définition incohérente, mal fondée, ou ambiguë au point de changer un résultat ;
- un algorithme qui ne réalise pas sa spécification, une terminaison non garantie, une complexité fausse ;
- deux résultats qui se contredisent, ou un résumé, une introduction ou une conclusion qui affirment plus que le corps ne démontre ;
- une formule ou un exemple calculé faux, même par faute de frappe, puisque le sens change.

Seules les erreurs suivent le protocole complet : graphe causal, contre-exemple, gardes, correction de bas en haut.

Les **défauts de forme** (typo hors formule, numérotation, renvoi, entrée bibliographique) ne sont pas des erreurs au sens de ce protocole. Ils suivent la voie éditoriale (phase 5), sans contre-exemple ni chaîne causale. Les préférences de style sont écartées.

## Paramètres

- `<document>` : le ou les fichiers audités.
- `--corpus <dossier>` : le corpus global de gardes. Par défaut, le corpus de vérification existant du projet s'il y en a un (en respecter les conventions), sinon `spec-guards/` à la racine.
- `--max-iter N` : nombre maximal d'itérations (défaut 5).
- `--auto` : appliquer aussi les corrections critiques sans pause (voir 4.3).
- `--resume` : reprendre un audit interrompu à partir de son registre, dans son worktree existant.
- `--base <réf>` : branche ou commit de départ du worktree (défaut : `HEAD` du dépôt courant).
- `--no-worktree` : travailler dans le répertoire courant, sans worktree, quand il est déjà isolé pour l'audit.
- `--keep` : à la clôture, ne poser aucune question et conserver le worktree ; seul le rapport est rapatrié (phase 8).

## Rôles

| Rôle | Qui | Voit | Écrit |
|---|---|---|---|
| Orchestrateur | toi | tout : registre, corpus, historique git | document, corpus, registre |
| Relecteur | agent `spec-reviewer`, neuf à chaque vague | le document et ses dépendances normatives, rien d'autre | rien, hors son brouillon |
| Arbitre | agent `spec-adjudicator`, neuf pour chaque erreur | une erreur et le document | rien, hors son brouillon |

Installés dans `~/.claude/agents/`, ces agents s'appellent `spec-reviewer` et `spec-adjudicator` ; installés comme plugin, `spec-audit:spec-reviewer` et `spec-audit:spec-adjudicator`. S'ils ne sont pas disponibles, lance un agent généraliste neuf en lui donnant comme consigne le contenu de `spec-reviewer.md` ou `spec-adjudicator.md` (dans `~/.claude/agents/`, ou dans le dossier `agents/` du plugin). N'utilise jamais un agent de type « fork » : il hériterait de la conversation, donc de l'historique.

## Phase 0 — Préparation (une fois)

1. **Règles du projet.** Lis `CLAUDE.md`, les conventions et la mémoire du projet : elles priment sur ce skill (en-têtes d'attribution, versionnement des documents, politique de push, périmètre de la théorie, statut des preuves).
2. **Convention de version.** Le projet corrige-t-il le document en place, ou crée-t-il une nouvelle révision (nouveau fichier, section d'historique) ? Suis la convention ; si elle n'est pas claire, pose la question une fois.
3. **Worktree dédié.** Sauf avec `--no-worktree`, tout l'audit se déroule dans un worktree git créé pour lui : le document y est modifié, le corpus y grandit, les commits y restent, sans toucher au répertoire de l'utilisateur ni aux sessions qui y travaillent en parallèle.
   - `<slug>` : le nom du document sans extension, en minuscules ASCII, mots séparés par des tirets.
   - Relève le chemin du dépôt d'origine, sa branche courante et son commit de tête, et note-les au registre : la clôture (phase 8) en dépend.
   - Relève `git status` du dépôt courant. Si le document, ses dépendances normatives ou le corpus ont des modifications non commitées, elles n'existeront pas dans le worktree : demande à l'utilisateur s'il faut auditer la version commitée ou s'il préfère commiter d'abord. N'utilise pas `git stash`, partagé entre tous les worktrees.
   - Nomme la branche `audit/<slug>` et le répertoire `<parent de la racine du dépôt>/<nom du dépôt>-audit-<slug>`. Si l'une ou l'autre existe déjà hors `--resume`, ajoute un suffixe `-2`, `-3`…
   - Crée-le : `git worktree add "<répertoire>" -b audit/<slug> <base>`, où `<base>` vaut `--base` ou `HEAD`. Avec `--resume`, retrouve-le plutôt par `git worktree list`.
   - Désormais, toutes les commandes s'exécutent dans le worktree (chemins absolus, ou `git -C "<répertoire>"`), et les agents reçoivent des chemins absolus dans le worktree.
   - Les fichiers non suivis par git (sources PDF, environnements, dépendances compilées) n'y sont pas : lis-les dans le dépôt d'origine, en lecture seule, et vérifie que le lanceur du corpus fonctionne dans le worktree avant de commencer.
   - Avec `--no-worktree`, travaille sur place, mais relève `git status` : d'autres sessions peuvent travailler en parallèle, et leurs modifications ne sont pas les tiennes.
   - Hors dépôt git, demande s'il faut en initialiser un : sans git, il n'y a ni isolation ni commits.
   - Dans tous les cas, ne commite que tes fichiers et ne pousse jamais.
4. **Registre.** Crée `spec-audit/<slug-du-document>/registre.md` (format dans `references/registre.md`), ou relis-le avec `--resume`. C'est la mémoire de l'audit : il doit survivre à une compaction du contexte, donc mets-le à jour après chaque étape, pas à la fin.
5. **Inventaire.** Établis `spec-audit/<slug>/inventaire.md` : chaque définition, lemme, proposition, théorème et algorithme, avec son énoncé et les résultats qu'il utilise. Ce graphe de dépendances sert à établir les liens causaux (phase 3), à propager les corrections (4.4) et à chercher les erreurs de même classe (4.2).
6. **État de référence.** Exécute tout le corpus. Il doit être vert ; une garde déjà rouge devient une erreur de l'itération 0, jamais un test à retoucher.
7. **Lint mécanique.** Écris une fois dans le corpus un script déterministe qui vérifie : continuité et unicité de la numérotation, existence de la cible de chaque renvoi, présence de chaque clé citée dans la bibliographie et citation de chaque entrée, équilibre des délimiteurs mathématiques, symboles employés avant leur définition quand c'est détectable. Il alimente la voie éditoriale.

## Phase 1 — Détection complète, à froid

Toutes les erreurs de l'itération sont détectées avant qu'aucune ne soit confirmée, testée ou corrigée : le classement causal (phase 3) n'a de sens que sur l'ensemble des erreurs.

Chaque relecteur est neuf et reçoit un message fixe qui ne dit rien de l'audit :

```
Relis intégralement ce document comme un rapporteur qui le découvre : <chemins>.
Dépendances normatives (définitions qu'il utilise) : <chemins, ou « aucune »>.
Angle : <intégral | logique et preuves | définitions, cadrage et cas limites | algorithmes et complexité>.
Répertoire de brouillon pour tes calculs : <brouillon/iter-k/relecteur-x>.
Rends ta liste au format prévu par tes instructions.
```

- N'y ajoute jamais le registre, le corpus, les erreurs précédentes, les zones corrigées ni le motif de l'audit. Attirer l'attention sur un passage, c'est déjà biaiser la relecture.
- **Première vague** : un relecteur intégral, plus des relecteurs par angle si le document est long ou dense. Chacun lit tout le document, car une incohérence se voit entre deux sections, pas dans une seule.
- **Vagues suivantes** : un relecteur intégral neuf. S'il apporte des erreurs nouvelles par rapport à l'union des vagues précédentes (après dédoublonnage, phase 2), lance une vague de plus. La détection est complète quand une vague n'apporte plus rien de nouveau, et s'arrête au plus tard à la troisième vague ; dans ce cas, note au registre « détection non saturée ».
- Si le document est trop long pour une lecture, découpe-le par sections, mais donne à chaque relecteur les sections de définitions et de notation et la liste des énoncés de l'inventaire (sans historique), et ajoute une passe dédiée à la cohérence entre sections.
- Ne modifie pas le document pendant la détection : tous les relecteurs d'une itération lisent le même état.

## Phase 2 — Tri et dédoublonnage

Oriente d'abord chaque constat : erreur (définition ci-dessus) ou défaut de forme (voie éditoriale, phase 5). Les suggestions de style sont écartées.

Pour chaque erreur, rédige une **empreinte** indépendante de la numérotation et des lignes, qui changent au fil des corrections : `[type] objet — défaut — témoin`. Exemple : `[énoncé faux] borne de la fusion partielle — ignore le cas k > n — n = 2, k = 3`.

Compare-la, sur le sens et non sur la lettre, aux autres constats de l'itération et aux entrées du registre :

- **Nouvelle** → statut DÉTECTÉ, phase 3.
- **Identique à une erreur CORRIGÉE** → **récidive** : arrêt (phase 7), sans recorriger.
- **Identique à une erreur RÉFUTÉE** → écartée. Si deux passes indépendantes la relèvent encore, le texte induit en erreur : ouvre un défaut de forme « ambiguïté » pour le clarifier sans en changer le sens.
- **Identique à une erreur INDÉCISE ou ESCALADÉE** → écartée, déjà en attente de l'utilisateur.
- **Même classe, autre instance** → nouvelle, liée à l'erreur d'origine.

## Phase 3 — Graphe des causes

Classe les erreurs détectées en chaînes de causalité. Comme une erreur peut avoir plusieurs causes et plusieurs conséquences, c'est un graphe orienté : un arc `A → B` signifie « A cause B ».

- **Il y a un arc `A → B`** quand le défaut de B vient de A : B cite ou applique A, ou hérite de sa définition, et son défaut disparaîtrait si A était juste tel qu'énoncé ; ou le contre-exemple de B est celui de A, ou en dérive ; ou le même cadrage manquant (hypothèse, restriction de contexte) se propage de A à B.
- **Une dépendance n'est pas une causalité** : B peut utiliser A et avoir sa propre erreur. Dans ce cas, pas d'arc.
- Appuie-toi sur l'inventaire et sur les causes probables signalées par les relecteurs. Justifie chaque arc en une phrase au registre.
- **Lien douteux** : pas d'arc, B est traitée comme une racine, mais l'ordre de traitement suit les dépendances de l'inventaire, donc B passe de toute façon après sa cause présumée.
- **Racines** : les erreurs sans cause ouverte.

**Boucle causale.** Si le graphe contient un cycle (A cause B qui cause A, directement ou non), arrête la vérification : aucune correction de plus, rapport immédiat à l'utilisateur avec les erreurs du cycle et la justification de chaque arc. Il n'y a pas de bas par où commencer : soit le document raisonne en cercle, soit l'analyse causale est fausse, et dans les deux cas la décision revient à un humain. Refais ce contrôle chaque fois que le graphe change (4.4, 4.5).

## Phase 4 — Correction de bas en haut

```
tant qu'il reste une erreur ouverte dans le graphe :
    racines courantes = erreurs ouvertes dont toutes les causes sont
                        CORRIGÉES, RÉFUTÉES ou RÉSOLUES
    pour chaque racine, dans l'ordre des dépendances de l'inventaire :
        4.1 confirmation → 4.2 gardes (rouge) → 4.3 correction (vert) → 4.4 propagation
    pour chaque conséquence dont toutes les causes sont traitées :
        4.5 réévaluation
    contrôle de cycle (phase 3)
```

Tant que sa cause n'est pas corrigée, une conséquence est **ignorée** : statut BLOQUÉE (par F-…), ni arbitrée, ni testée, ni corrigée. Son analyse porterait sur un texte qui va changer, et sa correction risquerait de compenser la cause au lieu de la réparer.

### 4.1 Confirmation

La racine part chez un arbitre neuf, avec l'erreur seule (sans l'identité du relecteur ni les autres erreurs), les chemins du document et un brouillon. N'arbitre pas toi-même, en particulier une erreur qui touche un passage que tu as corrigé : tu serais juge de ton propre travail.

- **CONFIRMÉE** (preuve exécutée à l'appui) → 4.2.
- **RÉFUTÉE** (avec la raison) → retire ses arcs sortants ; ses conséquences sans autre cause ouverte deviennent des racines.
- **INDÉCISE** (avec ce qui permettrait de trancher) → escaladée à l'utilisateur, aucune modification ; ses conséquences restent BLOQUÉES et figurent au rapport.

Une erreur de type « énoncé faux » exige un contre-exemple **exécuté** ; sinon elle redescend en preuve lacunaire ou en INDÉCISE.

Si l'arbitre nomme une **cause en amont**, la racine n'en était pas une : si cette cause est déjà une erreur du graphe, ajoute l'arc ; sinon ouvre une nouvelle erreur pour elle, en phase 3. La racine repasse BLOQUÉE derrière sa cause, et le contrôle de cycle est refait.

### 4.2 Documentation et gardes, avant la correction

Écris la garde avant la correction : écrite après, elle tend à tester la correction plutôt que l'erreur.

1. **Registre** : une entrée complète (format dans `references/registre.md`), cause probable comprise. La cause (hypothèse implicite, cas limite oublié, résultat voisin recopié…) dit où chercher les erreurs sœurs.
2. **Gardes**, dans le corpus :
   - **Garde témoin** : encode l'énoncé original et vérifie qu'il échoue sur le contre-exemple (elle documente l'erreur), puis que l'énoncé corrigé y tient.
   - **Variantes** : au moins deux cas de plus parmi les cas limites pertinents (vide, singleton, 0 et 1, égalités et ex aequo, doublons, valeurs extrêmes, valeur absente ou NULL, ordre non total, débordement), et un **quasi-cas** où l'énoncé original est vrai, qui protège contre une sur-correction.
   - **Vérification bornée** de l'énoncé corrigé : exhaustive sur un petit domaine, ou par propriétés avec graine fixe.
   - **Garde de classe** : cherche dans l'inventaire les énoncés exposés au même motif (même hypothèse oubliée, même cas limite, même quantificateur) et ajoute une garde pour chacun, même s'ils sont justes aujourd'hui. Un énoncé frère qui s'avère faux devient une nouvelle erreur, ajoutée au graphe.
   - **Preuve lacunaire** : une garde sur l'affirmation intermédiaire de l'étape fautive, testée sur des instances bornées sous les hypothèses disponibles à cet endroit.
3. **Rouge d'abord** : exécute la garde contre la formulation originale ; l'assertion sur l'énoncé original doit échouer, preuve que la garde détecte l'erreur. Consigne le résultat au registre.

Règles du corpus :
- il ne fait que grandir : ne supprime ni n'assouplis jamais une garde pour la faire passer ; toute modification d'une garde existante est justifiée au registre et signalée dans le rapport ;
- arithmétique exacte (entiers, rationnels, calcul symbolique), jamais d'égalité entre flottants ; graines fixes ;
- le modèle encodé dans la garde suit les définitions du document, pas la correction proposée ;
- respecte les conventions du corpus existant (en-têtes, nommage, lanceur de tests).

### 4.3 Correction

Choisis la nature de la correction, et consigne-la :

- **correctif d'énoncé** : la conclusion est affaiblie ou rectifiée ;
- **complément de cadrage** : une hypothèse est ajoutée, ou le contexte ou le domaine d'application est restreint, pour que l'énoncé redevienne vrai ;
- **complément ou réparation de preuve** : l'énoncé tient, l'étape fautive est justifiée ou remplacée.

Elles se combinent au besoin. Dans tous les cas :

- **Correction minimale** : le changement le plus faible qui rend l'énoncé vrai et garde ses usages valides. Ne renforce jamais un énoncé, n'introduis pas de résultat nouveau pour boucher un trou, ne supprime jamais un résultat en silence : un résultat retiré est marqué comme tel, avec la raison et le contre-exemple.
- **Corrections critiques** : modifier l'énoncé d'un résultat principal (théorème, résultat cité dans le résumé) ou retirer un résultat change ce que le document affirme. Par défaut, traite d'abord les racines non critiques, puis présente ensemble à l'utilisateur les corrections critiques en attente (énoncé avant et après, contre-exemple, impact) et attends son accord ; leurs chaînes restent BLOQUÉES jusque-là. Avec `--auto`, applique et signale-le dans le rapport.
- **Vert** : exécute la garde de l'erreur, puis tout le corpus. Une garde verte qui passe au rouge est une régression : annule la correction et repasse l'erreur en INDÉCISE.
- **Traçabilité** : si le document a une section d'errata, d'historique ou de révision, ou si le projet versionne ses documents, consigne la correction selon cette convention.

### 4.4 Propagation

À partir de l'inventaire, revérifie tout ce qui dépend de l'énoncé corrigé : résultats ultérieurs, preuves qui le citent, exemples, tableaux, résumé, introduction, conclusion, autres documents du projet, code ou mécanisation qui y renvoient. Un complément de cadrage oblige chaque utilisateur de l'énoncé à satisfaire la nouvelle hypothèse : chaque usage qui ne la satisfait plus devient une nouvelle erreur, conséquence de la racine (arc racine → nouvelle erreur), traitée dans la même boucle.

### 4.5 Réévaluation des conséquences

Quand toutes les causes d'une conséquence sont traitées, envoie-la à un arbitre neuf, qui la juge contre le texte corrigé :

- **RÉFUTÉE** → statut RÉSOLUE (par F-…). Ajoute son cas aux gardes de la cause : si la cause régressait, la conséquence le montrerait aussi.
- **CONFIRMÉE** → elle devient une racine et suit le protocole complet (4.2 à 4.4).
- **Changement de nature** → nouvelle erreur, ajoutée au graphe.

## Phase 5 — Voie éditoriale

Après les corrections de fond de l'itération, qui peuvent déplacer le texte et les numéros :

- relance le lint et corrige ce qu'il relève ;
- corrige les typos hors formules (orthographe, grammaire, mise en page) ; tout changement d'une formule, d'un symbole, d'un indice, d'un quantificateur ou d'une inégalité est une erreur, pas un défaut de forme ;
- **numérotation** : préfère la stabilité (insertion en 4.3′ ou 4.3a). Si une renumérotation est inévitable, mets à jour tous les renvois, internes et externes, et consigne la correspondance ancien → nouveau ;
- **bibliographie** : ne corrige une référence que contre sa source (PDF local, page de l'éditeur, DBLP…) ; sinon marque-la « à vérifier » et laisse-la telle quelle. N'invente jamais une métadonnée : pages, DOI, numéro de théorème ;
- pour chaque classe de défaut corrigée, ajoute une règle au lint, pour qu'elle soit désormais détectée mécaniquement.

## Phase 6 — Clôture de l'itération

Exécute tout le corpus et le lint : tout doit être vert. Commite localement dans le worktree (message listant les identifiants des erreurs et défauts traités), seulement tes fichiers, sans push. Mets à jour le journal du registre.

## Phase 7 — Boucle et arrêt

Reviens à la phase 1 avec de nouveaux agents. Arrête-toi à la première condition remplie :

1. **Convergence** : une détection complète à froid ne produit aucune erreur confirmée. Si l'itération précédente a modifié l'énoncé ou le cadrage d'un résultat, exige une seconde détection propre : c'est là que naissent les nouvelles erreurs.
2. **Boucle causale** : le graphe des causes contient un cycle (phase 3).
3. **Récidive** : une erreur est identique à une erreur déjà CORRIGÉE. Arrête sans recorriger : soit la correction n'a pas tenu, soit deux corrections se contredisent. Rapporte les deux entrées et le diff en cause.
4. **Oscillation** : une correction proposée annulerait, même en partie, une correction antérieure de l'audit ; ou une même correction a engendré deux erreurs confirmées successives.
5. **Non-convergence** : le nombre d'erreurs confirmées ne diminue pas sur deux itérations consécutives. Le document demande sans doute une reprise humaine plutôt que des rustines.
6. **Budget** : `--max-iter` atteint.
7. **Épuisement** : la détection ne relève plus que des défauts de forme. Termine la voie éditoriale, relance le lint et le corpus, puis arrête.

Ne conclus jamais « le document est correct ». Conclus « N détections indépendantes n'ont plus relevé d'erreur confirmée », en disant ce qui n'a pas été vérifié.

## Rapport final

Écris-le dans `spec-audit/<slug>/rapport.md`, dans le worktree ; le résumé à l'utilisateur vient avec la clôture (phase 8) :

```markdown
# Audit de précision — <document>

## Résultat
Motif d'arrêt, itérations, erreurs confirmées / réfutées / résolues par leur cause / indécises / bloquées, défauts de forme corrigés, commits.

## Graphe des causes
Par itération : racines, chaînes, et pour chaque arc sa justification. Cycle éventuel en tête.

## Énoncés modifiés
Pour chaque résultat touché : avant → après, nature (correctif, cadrage, preuve), contre-exemple, gardes.

## Erreurs
| ID | Gravité | Type | Causes | Statut | Correction | Gardes | Commit |

## Points ouverts
Indécises et chaînes qu'elles bloquent, références à vérifier, récidives, oscillations, gardes modifiées, corrections critiques en attente, détection non saturée.

## Corpus
Gardes ajoutées, règles de lint ajoutées, commande pour tout rejouer.

## Portée de la vérification
Ce qui a été vérifié et comment (relecture par agent, test exhaustif borné, preuve mécanisée), et ce qui ne l'a pas été.
```

Termine le rapport par la branche et le worktree (chemin, branche `audit/<slug>`, base, commits) et par l'issue de l'audit avec l'option de clôture recommandée (phase 8).

Une relecture par des agents et des tests bornés ne sont ni une relecture par les pairs ni une preuve. N'écris jamais qu'une preuve est « vérifiée » sans dire par quoi ; seule une preuve mécanisée peut être dite vérifiée par machine.

## Phase 8 — Clôture

La clôture se décide avec l'utilisateur, par une question à choix multiple, après qu'il a pu lire le rapport.

### 8.1 Classer l'issue

| Issue | Condition |
|---|---|
| **Succès** | arrêt par convergence ou épuisement ; corpus et lint verts ; aucune erreur INDÉCISE, aucune chaîne BLOQUÉE, aucune correction critique en attente |
| **Partiel, à poursuivre** | arrêt sur budget, ou détection non saturée ; corpus et lint verts |
| **Partiel, à arbitrer** | points qui attendent une décision humaine : erreur INDÉCISE, chaîne BLOQUÉE, correction critique refusée ou en attente ; corpus et lint verts |
| **Échec** | boucle causale, récidive, oscillation, non-convergence, corpus ou lint rouges, ou arrêt sur une erreur d'exécution |

### 8.2 Présenter le rapport

Résume l'audit dans la session (issue, motif d'arrêt, erreurs confirmées et corrigées, énoncés modifiés, points ouverts) et donne le chemin du rapport complet, `<worktree>/spec-audit/<slug>/rapport.md`, à lire avant de choisir.

### 8.3 Poser la question

Utilise l'outil de question à choix multiple (AskUserQuestion) : une seule question, d'en-tête « Clôture », qui rappelle l'issue et le chemin du rapport. Les options :

| Option | Effet |
|---|---|
| **Accepter et fusionner** | fusion de `audit/<slug>` dans la branche d'origine après les contrôles de sécurité (8.5), puis suppression du worktree et de la branche |
| **Refaire une vérification** | nouvelle série d'itérations dans le même worktree (8.7), sans rien fusionner |
| **Conserver le worktree** | ni fusion ni suppression ; rapport et patch archivés dans la branche d'origine ; décision reportée |
| **Abandonner** | rapport, registre et patch archivés dans la branche d'origine, puis suppression du worktree et de la branche (8.6) |

L'outil ajoute toujours une réponse libre (« Autre »).

Mets l'option recommandée en premier, avec « (recommandé) » à la fin de son libellé. C'est l'option la plus sûre pour l'issue :

| Issue | Recommandée | Proposées aussi | Pourquoi |
|---|---|---|---|
| Succès | Accepter et fusionner | Refaire, Conserver, Abandonner | chaque correction est confirmée et gardée, le corpus est vert |
| Partiel, à poursuivre | Refaire une vérification | Accepter, Conserver, Abandonner | une nouvelle série peut fermer les points restants sans toucher à la branche d'origine |
| Partiel, à arbitrer | Conserver le worktree | Accepter, Refaire, Abandonner | une nouvelle passe ne tranchera pas ce qui attend une décision humaine, et conserver ne perd rien |
| Échec | Abandonner | Conserver ; Accepter seulement si corpus et lint sont verts | le processus automatique ne peut plus progresser, et l'archive garde tout |

Règles :

- Ne propose jamais « Accepter » si le corpus ou le lint sont rouges.
- Ne propose pas « Refaire » après une boucle causale, une récidive, une oscillation ou une non-convergence : une nouvelle passe tournerait en rond. Après un « Refaire » qui n'a corrigé aucune nouvelle erreur, recommande « Conserver » plutôt que « Refaire ».
- Interprète une réponse libre ; si elle est ambiguë, repose la question. Ne fusionne et ne supprime jamais sur une réponse ambiguë.
- Si la question ne peut pas être posée (session non interactive), ou avec `--keep`, applique « Conserver le worktree » : c'est la seule option qui ne change rien et ne perd rien.
- Consigne au registre la question, l'option recommandée et la réponse.

### 8.4 Rapatrier le rapport

Dans tous les cas, avant toute suppression :

- **Dans la session** : le résumé de 8.2, complété par la clôture effectuée (commit de fusion, archive, worktree conservé ou supprimé).
- **Dans la branche d'origine** :
  - *Accepter* : le rapport, le registre, l'inventaire et les gardes arrivent avec la fusion.
  - *Conserver* ou *Abandonner* : commite d'abord dans le worktree tout travail en cours, avec un message qui le marque comme non vérifié. Copie ensuite dans le dépôt d'origine, sous `spec-audit/<slug>/<AAAA-MM-JJ>-<issue>/`, le `rapport.md`, le `registre.md` et un `corrections.patch` produit par `git -C "<worktree>" diff <base> audit/<slug>`. Ce patch contient les corrections et les gardes : rien n'est perdu, même après l'abandon. Commite seulement ces fichiers (`git add -- <chemins>` puis `git commit -m "<message>" -- <chemins>`), pour n'embarquer aucune modification d'une autre session. Si les règles du projet interdisent ce commit, laisse les fichiers non commités et dis-le.
  - *Refaire* : rien pour l'instant ; le rapport de la série suivante passera par cette même clôture.

N'abandonne jamais un worktree avant que ce rapatriement ait réussi.

### 8.5 Fusion (« Accepter et fusionner »)

1. Vérifie que le dépôt d'origine est toujours sur la branche relevée en phase 0. Sinon, ne fusionne pas : conserve le worktree et repose la question.
2. Si la branche d'origine a avancé depuis la base, intègre-la dans le worktree : `git -C "<worktree>" merge <branche d'origine>`. En cas de conflit, `git merge --abort`, conserve le worktree et rapporte que la fusion est bloquée ; l'audit, lui, n'a pas échoué.
3. Relance tout le corpus et le lint dans le worktree : tout doit être vert, sinon conserve le worktree et rapporte.
4. Fusionne dans le dépôt d'origine : `git -C "<dépôt d'origine>" merge --no-ff audit/<slug> -m "<message selon les conventions du projet>"`. La branche d'audit contenant déjà la tête d'origine, il n'y a plus de conflit possible ; si git refuse à cause de modifications non commitées dans le dépôt d'origine, ne force pas et ne stashe pas : conserve le worktree et rapporte.
5. Supprime le worktree (`git worktree remove "<worktree>"`), puis la branche (`git branch -d audit/<slug>`, qui refuse de supprimer une branche non fusionnée).
6. Ne pousse jamais.

### 8.6 Abandon (« Abandonner »)

Après le rapatriement : `git worktree remove --force "<worktree>"`, puis `git branch -D audit/<slug>`. Le patch archivé permet de rejouer tout ou partie des corrections, ou de les examiner.

### 8.7 Nouvelle vérification (« Refaire une vérification »)

Reprends à la phase 1 dans le même worktree, avec de nouveaux agents et un nouveau budget égal à `--max-iter`. Le registre continue (les identifiants ne sont jamais réattribués), les gardes restent en place, et la série se termine à nouveau par cette phase 8.

### 8.8 Interruption

Si la session s'interrompt avant la clôture (erreur, arrêt par l'utilisateur), le worktree et la branche restent en place : `--resume` reprend l'audit, ou la phase 8 peut être rejouée seule.
