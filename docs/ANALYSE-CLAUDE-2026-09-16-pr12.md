# Analyse Claude — PR #12 (lot 2b-1) — 2026-09-16

> **Écrite et figée AVANT lecture du rapport Codex.** C'est la seule chose qui
> donne une valeur à une convergence : sans horodatage, « j'avais trouvé pareil »
> ne vaut rien. Règle : `rules/roles-claude-codex.md`, § 4 bis.
>
> Branche `lot/2b-referentiels` (`58a6712`), 221 tests verts.

## Ce que j'ai mesuré, et comment

Trois mesures, toutes par **chemin indépendant** du code audité.

### M1 — L'ordre naturel de SQLite diverge-t-il de l'ordre des identifiants ?

Banc : table `INTEGER PRIMARY KEY`, insertion, suppression d'un id intermédiaire
puis réinsertion, suppression du maximum puis réinsertion, identifiant explicite
à 2000, puis `VACUUM`.

| Étape | Ordre naturel rendu | Trié ? |
| --- | --- | --- |
| insertion simple | `1 2 3 4 5` | oui |
| suppression de 3 + insertion | `1 2 4 5 6` | oui — **l'id n'est pas réutilisé** |
| suppression du max + insertion | `1 2 4 6 7` | oui |
| id explicite 2000 puis auto | `1 2 4 6 7 2000 2001` | oui |
| après `VACUUM` | `1 2 4 6 7 2000 2001` | **oui** |

**Conclusion** : sur une table à `rowid`, un `SELECT` sans `ORDER BY` parcourt
l'arbre B **dans l'ordre du rowid**, donc dans l'ordre des identifiants — y
compris après suppression, réinsertion et `VACUUM`. C'est pourquoi la mutation
« retirer `order_by` » reste verte, et ce n'est pas un hasard.

**MAIS** : la même mesure montre qu'une requête servie par un **index** rend ses
lignes dans l'ordre de l'index, pas du rowid (plan relevé :
`SEARCH t USING COVERING INDEX`). Or le lot 2c filtrera les référentiels sur
`actif` pour l'optimisation. **Le jour où un `WHERE` permet au planificateur de
choisir un index, l'ordre diverge et la pagination saute des éléments.**

→ `order_by(id)` est **correct et doit rester**. Ce n'est pas une précaution
inutile : c'est une garantie qui ne se voit pas encore.

### M2 — Le `downgrade` est-il réellement réversible ?

Banc : base vierge, `upgrade head` → capture du **DDL complet** de
`sqlite_master` → `downgrade -1` → `upgrade head` → seconde capture, comparaison.

```
objets au depart : 12   apres downgrade : 4   apres remontee : 12
DDL identique apres aller-retour : True
```

Le `downgrade` retire exactement les 6 tables du lot **et les 2 index**
(`ix_cylindre_machine_id`, `ix_outil_cylindre_id`) ; la remontée les rend à
l'identique, contraintes `UNIQUE` et clés étrangères comprises.

**Conclusion** : réversible pour de vrai, pas seulement « la table revient ».
⚠️ Le test du dépôt, lui, ne compare que des **noms de tables** : il ne verrait
pas un index perdu. Écart entre ce que le test prouve et ce que j'affirme ici.

### M3 — Le `PUT` en remplacement complet a-t-il un bord tranchant ?

Sonde sur l'API réelle : création d'une machine **désactivée** avec deux modules,
puis `PUT` ne renvoyant pas `actif` ni `modules` — le geste d'un front qui
n'envoie que ce qu'il a modifié.

```
1. cree desactive, avec modules : False ['vernis', 'dorure']
2. PUT sans 'actif' ni 'modules' -> 200
   actif  : False -> True
   modules: ['vernis', 'dorure'] -> []
3. PUT sans un champ REQUIS      -> 422 (payload_invalide)
```

## Mes constats — avant toute lecture du rapport

### C-A — `PUT` : les champs à valeur par défaut sont silencieusement réinitialisés — **ÉLEVÉ**

**Fichier** : `app/schemas/referentiels.py`, `app/routers/referentiels.py::remplacer`.

Un champ **requis** omis rend 422 : le remplacement complet est protégé de ce
côté. Mais les champs **porteurs d'un défaut** ne le sont pas. Ils sont
nombreux : `actif`, `modules`, `modules_requis`, `forme_speciale`,
`silhouette_automatique`, `groupes_couleurs_requis`, `nb_dents`,
`date_inventaire`, `contact`, `email`, `telephone`.

**Impact, et il est métier, pas cosmétique** : la règle du produit est « on ne
supprime pas, on **désactive** » — c'est elle qui protège l'histoire des devis
déjà envoyés. Or **n'importe quel `PUT` qui oublie `actif` réactive l'élément**,
sans erreur et sans trace. Une machine mise hors parc ressort proposée à
l'optimisation ; un client archivé redevient actif. La désactivation est donc une
protection qu'un enregistrement distrait défait.

Second effet mesuré : `modules` repart à `[]`. Les modules sont un **filtre dur**
pour les options — une machine vidée de ses modules devient invisible pour toute
option qui en exige un, et le devis choisit une autre presse sans rien signaler.

**Correction envisagée (minimale)** : rendre obligatoires, dans les schémas
d'écriture, les champs dont la perte est silencieuse — au minimum `actif` et les
listes. Un front qui repose l'objet lu les envoie déjà ; un front qui les oublie
reçoit alors un 422 explicite au lieu d'une réinitialisation muette. Coût : un
front qui construisait un corps partiel passe de « ça marche à moitié » à « 422 ».
C'est le but.

**Risque de la correction** : faible. Elle durcit une entrée, elle ne change
aucune sortie ; elle est visible immédiatement côté front (422), jamais
silencieuse.

### C-B — Le test d'aller-retour de migration ne compare que des noms de tables — **MOYEN**

**Fichier** : `backend/tests/test_migration_referentiels.py`.

Il affirme « aller-retour vérifié » et ne vérifie que la présence de tables. M2
montre que le DDL revient réellement à l'identique — mais **le test ne le
prouve pas**. Un `downgrade` qui oublierait un index passerait au vert.

C'est le même défaut de forme que l'`order_by` : un contrôle qui annonce plus
que ce qu'il mesure.

### C-C — `order_by(id)` : le code est juste, le test est creux — **FAIBLE (déjà documenté)**

Le code est correct (M1). Le test ne peut pas attraper son absence, et son
docstring le dit déjà. Rien à corriger dans le code ; la seule chose qui pourrait
l'améliorer serait un test qui force un plan d'exécution par index, ce qui
testerait le planificateur de SQLite plutôt que notre code. **Je ne le
recommande pas.**

### C-D — `_commettre` peut rendre 500 sur un chemin non atteignable aujourd'hui — **FAIBLE**

Si `IntegrityError` survient sans qu'une clé en conflit soit retrouvée,
l'exception est relancée → 500. Les clés étrangères étant pré-validées et les
`NOT NULL` couverts par Pydantic, je n'ai **pas** trouvé de chemin atteignable
hors course. Le comportement (erreur franche plutôt que diagnostic inventé) me
paraît juste. **Rien à corriger.**

### C-E — `est_reference()` : couverture correcte, point d'extension unique — **RIEN À SIGNALER**

`DELETE /{id}` du routeur générique est le **seul** chemin de suppression de
l'API. Aucun `relationship()` n'est déclaré entre les six modèles, donc aucune
cascade ORM ; aucune clé étrangère ne porte `ON DELETE CASCADE`, donc aucune
cascade SQL. Les deux relations existantes (machine→cylindre, cylindre→outil)
sont bien couvertes. Le lot 2c étend `LIENS`, et c'est le seul point à toucher.

## Ce que j'attends de Codex

Les points où mon analyse est **la plus faible**, et où je veux être contredit :

- la question 2 du brief (les « précisions » sont-elles vraiment des précisions) :
  je suis juge et partie, c'est moi qui les ai écrites ;
- la sémantique des deux `PUT` : je la défends, donc je la vois mal ;
- tout ce qui touche à la concurrence : le projet est mono-utilisateur sur
  SQLite, et j'ai tendance à écarter ces cas un peu vite.
