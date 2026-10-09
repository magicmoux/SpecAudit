# Format du registre et des gardes

## En-tête du registre (`spec-audit/<slug>/registre.md`)

```markdown
# Registre d'audit — <document>

- Document(s) : <chemins>
- Dépendances normatives : <chemins>
- Corpus : <dossier>, lanceur : <commande>
- Dépôt d'origine : <chemin>, branche <nom>, tête <hash>
- Worktree : <chemin>, branche audit/<slug>, base <hash>
- Paramètres : max-iter = N, auto = oui/non
- Convention de version : correction en place | nouvelle révision <nom>

## Journal des itérations

| Itér. | Vagues de détection | Saturée | Erreurs détectées | Racines | Confirmées | Réfutées | Résolues par leur cause | Indécises | Bloquées | Défauts de forme | Gardes ajoutées | Corpus | Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Graphe des causes — itération <k>

Arcs « cause → conséquence », un par ligne, chacun justifié :

- F-k-1 → F-k-4 : la Proposition 4.6 applique le Lemme 4.3, faux pour k > n ; son contre-exemple est le même.
- F-k-1 → F-k-7 : …

Racines initiales : F-k-1, F-k-2. Ordre de traitement : F-k-2, F-k-1 (dépendances de l'inventaire).
Cycle : aucun | <erreurs du cycle> → arrêt.

## Erreurs

## Défauts de forme
```

## Entrée d'erreur

```markdown
### F-<itération>-<n> — <titre court>

- **Empreinte** : [type] objet — défaut — témoin
- **Statut** : DÉTECTÉE | BLOQUÉE (par F-…) | CONFIRMÉE | RÉFUTÉE | INDÉCISE | CORRIGÉE | RÉSOLUE (par F-…) | ESCALADÉE | RÉCIDIVE
- **Type** : énoncé faux | preuve lacunaire | cadrage insuffisant | définition | algorithme ou complexité | incohérence
- **Gravité** : critique (résultat faux) | majeure (preuve lacunaire, hypothèse manquante) | mineure (imprécision locale)
- **Localisation** : section, et citation exacte du passage (deux lignes au plus)
- **Description** : ce qui est faux, et pourquoi
- **Causes** : F-… (avec la justification de l'arc), ou « racine »
- **Conséquences** : F-…
- **Cause probable** : hypothèse implicite, cas limite oublié, résultat voisin recopié, notation surchargée…
- **Contre-exemple(s)** : instance minimale, résultat attendu selon le texte, résultat obtenu, chemin du script
- **Verdict de l'arbitre** : résumé, et raison du rejet le cas échéant
- **Impact** : résultats et passages dépendants (d'après l'inventaire)
- **Gardes** : chemins dans le corpus ; état rouge avant correction, vert après
- **Correction** : nature (correctif d'énoncé | complément de cadrage | complément de preuve) ; avant → après ; commit
- **Liens** : erreurs de la même classe
```

Les identifiants ne sont jamais réattribués. Une erreur réfutée reste au registre : c'est elle qui permet d'écarter le même faux positif à la passe suivante.

## Entrée de défaut de forme

```markdown
- D-<itération>-<n> — <typo | numérotation | renvoi | bibliographie | ambiguïté> — <localisation> — <avant → après> — <source pour la bibliographie, ou « à vérifier »> — <règle de lint ajoutée>
```

## Fichier de garde (exemple en Python, à adapter au lanceur du projet)

```python
# Garde F-2-3 — [énoncé faux] borne de la fusion partielle — ignore le cas k > n — n = 2, k = 3
# Énoncé original : <citation>
# Énoncé corrigé  : <citation> (complément de cadrage : k ≤ n)
# Modèle : définitions du §2 du document, encodées sans référence à la correction.
# Conséquences couvertes : F-2-5 (Proposition 4.6), résolue par cette correction.
from fractions import Fraction

def enonce_original(instance): ...
def enonce_corrige(instance): ...

def test_F_2_3_original_refute_par_le_temoin():
    assert not enonce_original(TEMOIN)

def test_F_2_3_corrige_tient_sur_le_temoin_et_les_variantes():
    for cas in [TEMOIN, *VARIANTES]:
        assert enonce_corrige(cas)

def test_F_2_3_quasi_cas_ou_l_original_est_vrai():
    assert enonce_original(QUASI_CAS) and enonce_corrige(QUASI_CAS)

def test_F_2_3_corrige_exhaustif_sur_domaine_borne():
    for cas in domaine(taille_max=4):
        assert enonce_corrige(cas), cas

def test_F_2_5_consequence_tient_sur_le_temoin_de_la_cause():
    assert proposition_4_6(TEMOIN)
```
