# Analyse Claude — PR #13 (lot 2b-2) — figée AVANT lecture du rapport Codex

Branche `lot/2b-parametres` (`45319ef`), base `lot/2b-referentiels`.
Méthode : **exécution** (sondes + suite de tests), pas relecture.
Suite rejouée par moi : **260 passés, code retour 0** — l'annonce du brief est reproduite.

## C-1 — MOYEN — `assurer_baremes()` n'est PAS idempotent sous concurrence → 500

Le docstring affirme « idempotent et se répare tout seul : une ligne manquante
ne peut jamais casser un écran ». **Mesuré faux.**

Reproduit avec deux sessions réelles, A et B, dans la vraie fenêtre (A lit,
B lit, B commite, A commite) :

```
A execute assurer_baremes() ... (commit retarde)
B execute assurer_baremes() ... OK, B a commite.
A commite enfin ... IntegrityError NON RATTRAPEE
   -> UNIQUE constraint failed: bareme.type
baremes en base a la fin : 4 (pas de doublon : `type` est la cle primaire)
```

Aucun `try/except` dans `assurer_baremes()` ni dans le routeur → **HTTP 500**
sur `GET /api/baremes`, le tout premier appel de l'écran barèmes.

**Portée réelle, et c'est ce qui borne la gravité** : la fenêtre n'existe que
tant que des barèmes manquent, c'est-à-dire **une seule fois**, au premier accès
après déploiement. Ensuite `manquants` est vide et la fonction sort tout de
suite. Aucune corruption : la clé primaire empêche le doublon.

**Mais c'est la démo publique** qui est multi-utilisateur, et le premier accès
après déploiement est exactement le moment où plusieurs visiteurs arrivent.

**Correction** : `except IntegrityError` → `rollback` → relire (les lignes
existent alors). Trois lignes. **C'est la même famille que le constat 7 de la
PR #12** (course sur `DELETE`), corrigé ce matin.

## C-2 — MOYEN — `neutre` est faux dès qu'une valeur de `donnees` est *falsy*

`neutre = not any(bool(valeur) for valeur in donnees.values())`. Mesuré sur
10 formes ; **4 écarts** :

```
{'coefficient': 0}                  neutre=True   <- coefficient REGLE a zero
{'coefficient': 0.0}                neutre=True
{'decalage_mm': 0, 'points': []}    neutre=True
{'actif_courbe': False}             neutre=True   <- booleen REGLE a faux
```

Un barème **délibérément calibré à zéro** se déclare non calibré. Le front
affiche alors « score indicatif » sur un barème réglé — ou l'inverse selon la
lecture qu'il en fait. Le contrat dit que `neutre` commande cet affichage, et
qu'un score indicatif présenté comme réglé fait « prendre une décision de prix
sur un chiffre qui ne veut rien dire ».

**Cause racine** : `donnees` est un **dictionnaire libre, non spécifié au
contrat**, et on en dérive un booléen métier affiché à l'utilisateur.
`donnees: dict` est bien imposé par Pydantic — un non-dict ne peut pas produire
de 500, ce point-là est fermé.

**Correction** : soit spécifier la forme de `donnees` au contrat et calculer
`neutre` sur une clé connue (`points`), soit assumer et l'écrire. La première
est préférable : `neutre` est du métier affiché, pas de la commodité.

**Réserve honnête** : la gravité dépend de ce que le front enverra, et il n'est
pas écrit. À trancher avec CC2.

## C-3 — MOYEN — l'exemption du mode démo est posée sur le ROUTEUR, pas sur la route

`routers/calibration.py` omet volontairement `interdire_ecriture_demo`, et
l'argument est juste **pour l'endpoint d'aujourd'hui** : vérifié, `taux_machine`
ne prend pas `db`, il ne peut rien écrire.

Le défaut n'est pas là. L'exemption vit sur `APIRouter(dependencies=[...])` :
**toute route ajoutée demain à ce routeur en hérite**. Un futur
`POST /api/calibration/appliquer` qui écrirait serait accessible en mode démo
**en silence** — le commentaire dit « le jour où cet endpoint écrira, la garde
doit revenir », mais rien ne le fera tomber.

Le test existant (« il répond en mode démo ») ne couvre que la route actuelle.

**Correction** : un test qui énumère les routes de l'application et exige que
toute route d'écriture non couverte par `interdire_ecriture_demo` figure dans
une **liste d'exemptions nommée**. Ajouter une route au routeur devient alors
rouge. Coût : un test.

## C-4 — MOYEN — le test d'aller-retour ne défait plus que la DERNIÈRE migration

`TABLES_DERNIERE_MIGRATION = {"bareme"}` et `downgrade -1`. Le test
`test_l_aller_retour_de_migration_se_joue_sur_une_base_vierge` n'exerce donc
plus que la réversibilité de `38af14d3d6c7`. **L'aller-retour de la migration
des référentiels n'est plus exercé par ce test** — son nom annonce plus que ce
qu'il prouve.

C'est aggravé par la correction du constat 3 de la PR #12, commitée ce matin :
elle ajoute la comparaison de **DDL complet** sur l'aller-retour... que ce test
ne joue plus sur les référentiels.

**Correction** : jouer l'aller-retour **migration par migration**, ou au moins
`downgrade base` puis `upgrade head` en comparant le DDL complet.

## C-5 — INTÉGRATION — la #13 ne contient pas les corrections de la #12

`lot/2b-parametres` est empilée sur un état **antérieur** à `1f969b4`
(corrections de l'audit #12). Fusion d'essai jouée :

```
code retour merge = 1
Auto-merging backend/app/routers/referentiels.py           -> OK
Auto-merging backend/tests/test_migration_referentiels.py  -> OK
CONFLICT (content): docs/CONTRAT-API.md
```

**Bonne nouvelle mesurée** : le correctif du `PUT` (`entree: r.remplacement`) et
celui du `DELETE` (`IntegrityError` → 409) **survivent intacts** à la fusion
automatique, ainsi que le test `_schema()`.

**Le conflit est documentaire, et il est exactement au mauvais endroit** : le
journal des changements v1.2, là où j'ai posé le bloc « ⚠️ CASSANT » destiné à
CC2. Une résolution pressée le fait disparaître. À résoudre à la main, en
vérifiant que le bloc survit.

## Points sans constat

- **Point 5 — formule du taux.** Aucun défaut. L'exemple du contrat est **exact
  au centime**, vérifié en exécutant la vraie fonction : 240000/10/1600 = 15,00 ·
  12000/1600 = 7,50 · 8000/1600 = 5,00 → 27,50, et la somme des lignes égale le
  taux rendu. L'écart annoncé « au plus un centime » entre somme-des-arrondis et
  total-arrondi-une-fois est **borné pour de vrai** : les résidus sub-centime des
  trois lignes se reportent sur le total, l'écart ne peut pas atteindre deux
  centimes. Pire écart trouvé par recherche : 0,01.
- **Points 1 et 2 — `marge_confort_roulage_mm` en entier.** **Défendable**, et
  c'est la différence avec le constat 2 de la PR #12 : l'annonce du 20/08 montrait
  ce champ à `null`, comme **neuf des dix**. Aucun type n'en était déductible,
  donc « précision » est le bon classement. ⚠️ Nuance : un front qui a suivi la
  règle générale « les décimaux sortent en chaîne » l'aura typé `string | null`
  et cassera sur `3`. Le piège est réel mais moindre, et la ligne 60 du contrat
  le dit explicitement. À signaler à CC2, pas à reclasser.
- **Point 3 — deux sémantiques de `PUT`.** Pas d'ambiguïté : les routes diffèrent.
  Depuis la correction de la #12, l'asymétrie est plus tranchée (référentiels =
  tout obligatoire, paramètres = partiel) donc plus lisible, pas moins.
- **Point 7b — le `db.commit()` au milieu d'une requête.** Bénin **aujourd'hui** :
  `assurer_baremes()` est appelé en première instruction des deux handlers, il n'y
  a rien d'autre en attente. C'est un piège latent, pas un défaut : à noter, pas à
  corriger.

## Ce que je n'ai PAS regardé

Volumétrie · comportement si la ligne `parametres_couts` manque · `machines_ids`
avec une machine désactivée · contenu de `donnees` au-delà des 10 formes sondées.
