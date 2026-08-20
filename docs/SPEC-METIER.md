# Cahier de recette métier — FlexoSuite v2

> **À quoi sert ce document.** FlexoSuite est réécrit depuis zéro. De l'ancien
> dépôt on ne reprend **aucune ligne de code** : seulement le **métier**, extrait
> ici. Ce fichier doit être assez précis pour écrire le moteur **sans jamais
> rouvrir l'ancien dépôt**.

> ## ⛔ Règle de confidentialité — lire avant d'ajouter quoi que ce soit
>
> **Ce document ne contient aucun chiffre d'atelier réel, et n'en contiendra
> jamais.** Ni tarif, ni barème réglé sur un parc de presses existant, ni nom
> d'entreprise, ni en commentaire.
>
> Ce qui se publie : les **formules**, les **invariants**, la **chaîne de pose**,
> la **structure** des barèmes. C'est de la convention professionnelle flexo.
> Ce qui ne se publie pas : les **valeurs** d'un atelier qui les a payées.
>
> Les paramètres de ce document sont un **jeu doré fabriqué** — arbitraire et
> manifestement fictif, en **deux ateliers** : l'un tout rond pour la lisibilité,
> l'autre délibérément non rond pour exercer les arrondis.
>
> **Le garde-fou est un test de ce qu'on livre, pas une liste de mots interdits** —
> une telle liste publierait exactement ce qu'elle prétend protéger. Ce qui est
> vérifié en CI : le seed d'installation ne contient **aucun tarif**, et toute
> valeur chiffrée de tarif vit dans **un unique module de fixtures fictives**.
> Voir `tests/test_confidentialite_livraison.py`.

---

## 1. Comment les valeurs de référence ont été fabriquées

Le principe habituel — figer des montants en tests de non-régression — est
conservé. Ce qui change, c'est **d'où viennent les nombres**.

1. On choisit des **jeux de paramètres manifestement fictifs** (§ 2) — l'un rond,
   l'autre non, pour que les tests exercent aussi la gestion des centimes.
2. On le passe dans l'**ancien moteur, en local**, avec la **structure** des
   payloads de référence — la géométrie et les quantités sont du métier, les
   tarifs n'en sont pas.
3. Les montants obtenus deviennent les **valeurs de référence** de ce dépôt.

**La preuve de non-régression tient** : même moteur, mêmes formules, autres
paramètres. Le nouveau moteur doit retomber sur ces montants au centime.

**Pas de vérification croisée avec une baseline antérieure** : elle n'apporterait
rien. Les attendus sortent d'un moteur déjà validé — c'est ce qui leur donne
autorité, et ils se recontrôlent à la main poste par poste (§ 5).

⚠️ Toute re-baseline ultérieure reste soumise à validation explicite d'Eric : un
écart se **signale**, il ne se corrige pas en changeant l'attendu.

## 2. Le jeu doré — deux ateliers fictifs

Le jeu doré comporte **deux** jeux de paramètres, et les deux sont nécessaires.

| | **Atelier Démo A** | **Atelier Démo B** |
| --- | --- | --- |
| Paramètres | tout est **rond** | rien n'est rond, **volontairement** |
| Ce qu'il prouve | les formules, recontrôlables à la main | **la gestion des centimes** |
| Usage | démo publique, lecture des tests | non-régression fine |

**Pourquoi le second existe.** Un jeu tout rond donne un total rond : agréable à
vérifier, mais **aveugle** précisément là où un moteur réécrit dérive — arrondis
intermédiaires, `Decimal` contre flottant, **ordre des opérations**. L'Atelier B
exerce tout cela : divisions non terminantes, arrondi de chaque poste, et arrondi
final qui mord (`1 245,22 × 1,275 = 1 587,6555` → **1 587,66**).

### Atelier Démo A — paramètres de coûts

| Paramètre | Valeur dorée |
| --- | ---: |
| `marge_standard_pct` | 25,00 |
| `cout_exploitation_machine_eur_h` | 300,00 |
| `cout_operateur_eur_h` | 60,00 |
| `cout_energies_eur_h` | 5,00 |
| `cout_fixe_atelier_eur_mois` | 2 000,00 |
| `cout_fixe_maintenance_eur_mois` | 500,00 |
| `buffer_rebut_pct` | 2,00 |
| `buffer_setup_pct` | 1,00 |
| `marge_confort_roulage_mm` | 20 |
| `cliche_prix_couleur_eur` | 40,00 |
| `outil_base_eur` | 250,00 |
| `outil_par_trace_eur` | 60,00 |
| `surcout_forme_speciale_facteur` | 1,50 |
| `calage_forfait_eur` | 200,00 |
| `finitions_prix_m2_eur` | 0,2000 |

### Atelier Démo A — données de référence

| Objet | Valeur dorée |
| --- | --- |
| Matière « Papier Démo 100 » | 100 g/m², 0,50 €/m² → **5,00 €/kg** |
| Presse « Presse Démo A » | `vitesse_moyenne_m_h` = 5 000 · `duree_calage_h` = 2,00 |
| Encre quadri | 20,00 €/kg · ratio 2,000 g/m²/couleur |
| Encre Pantone | 25,00 €/kg · ratio 2,000 g/m²/couleur |
| Forfait de sous-traitance | 100,00 € |

### Atelier Démo B — le jeu qui exerce les arrondis

| Paramètre | Valeur | | Paramètre | Valeur |
| --- | ---: | --- | --- | ---: |
| `marge_standard_pct` | 27,50 | | `cliche_prix_couleur_eur` | 37,80 |
| `cout_exploitation_machine_eur_h` | 287,45 | | `outil_base_eur` | 243,70 |
| `cout_operateur_eur_h` | 58,90 | | `outil_par_trace_eur` | 57,30 |
| `cout_energies_eur_h` | 4,30 | | `surcout_forme_speciale_facteur` | 1,35 |
| `cout_fixe_atelier_eur_mois` | 2 150,00 | | `calage_forfait_eur` | 193,60 |
| `cout_fixe_maintenance_eur_mois` | 640,00 | | `finitions_prix_m2_eur` | 0,1875 |
| `buffer_rebut_pct` | 2,30 | | `marge_confort_roulage_mm` | 15 |
| `buffer_setup_pct` | 1,10 | | | |

| Objet | Valeur |
| --- | --- |
| Matière « Papier Démo 90 » | **90,5 g/m²**, **0,4275 €/m²** → 4,723756906… €/kg *(division non terminante — c'est le but)* |
| Presse « Presse Démo B » | `vitesse_moyenne_m_h` = **4 730** · `duree_calage_h` = 1,75 |
| Encre quadri | 18,65 €/kg · ratio **2,150** g/m²/couleur |
| Encre Pantone | 23,40 €/kg · ratio 2,150 g/m²/couleur |
| Forfait de sous-traitance | 87,35 € |

> ⚠️ **Ce jeu doré n'est PAS le paramétrage livré au client.** L'application part
> **à zéro tarif** : un assistant de calibration les fait produire à
> l'installation, à partir des chiffres que l'imprimeur connaît (amortissement de
> presse, heures productives, énergie, maintenance ; grille de la convention
> collective des industries graphiques ; catalogue de son photograveur). Livrer
> les tarifs d'un atelier qui n'est pas le sien produirait des devis faux.
>
> Seule exception assumée : la **marge par défaut à 30 %**, décision commerciale,
> **confirmée explicitement** par l'imprimeur à l'installation. Aucun devis ne se
> calcule sur une marge qu'il n'a jamais vue.

## 3. Le calcul d'ensemble

```
cout_revient  = arrondi_2déc( Σ P1..P7 )
prix_vente_ht = arrondi_2déc( cout_revient × (1 + marge) )
```

**Il y a bien deux arrondis** : le coût de revient est arrondi **avant** que la
marge s'applique. La carte complète est au **§ 3 bis**.

Tous les calculs intermédiaires sont en `Decimal` — **jamais** en flottant.

### ⚠️ Convention de marge — à écrire noir sur blanc, et à afficher à l'imprimeur

`× (1 + pct)` est une **marge sur coût de revient** — un coefficient — **et non un
taux de marque**. La distinction n'est pas académique : elle se paie en argent.

| Ce que l'imprimeur lit | Ce qu'il comprend peut-être | Le prix qui en sort |
| --- | --- | --- |
| « marge 30 % » | **marge sur coût** (notre convention) | `1,30 × coût` |
| « marge 30 % » | **taux de marque** — 30 % du prix de vente | `coût / 0,70` = `1,4286 × coût` |

Un imprimeur qui lit « 30 % » comme un taux de marque attend un coefficient de
**1,4286** et facture en réalité **1,30** : soit **9 % en dessous** de ce qu'il
croit encaisser, sur chaque devis, sans que rien ne le signale.

**Ce qui en découle pour l'assistant de calibration** : il n'affiche **jamais** le
seul pourcentage. Il montre la **formule** et le **coefficient obtenu** —
« marge 30 % sur coût de revient → prix = coût × **1,30** » — et fait confirmer.
Le passage d'un taux de marque à notre convention se fait par
`pct = marque / (1 − marque)`.

**Où la marge se lit** (constaté dans l'ancien code, pas supposé) :
`ConfigCouts.marge_standard_pct`, stockée en **pourcentage** (0–100) et convertie
en fraction. **Ni** `Entreprise.pct_marge_defaut`, **ni** une constante de repli —
les deux existaient et ont été retirées. Priorité : override porté par le devis,
sinon paramètres. **Pas de troisième niveau** : sans paramètres, le moteur lève une
erreur explicite plutôt que de fabriquer un prix.

## 3 bis. Où l'arrondi tombe — la carte, poste par poste

> **L'arrondi se reproduit, il ne se normalise pas.** Les montants dorés sortent de
> l'ancien moteur **avec son arrondi**, incohérences comprises. Uniformiser est un
> chantier **séparé**, décidé après coup, avec re-baseline explicite. **Un montant
> doré ne se retouche jamais pour faire tomber un calcul.**

Tous les arrondis sont à **2 décimales**. Ce qui change d'un poste à l'autre, c'est
**combien de fois** on arrondit et **à quel moment**.

| Poste | Où l'arrondi tombe | Nombre d'arrondis |
| --- | --- | ---: |
| **P1 Matière** | une seule fois, sur `poids × prix_kg` | 1 |
| **P2 Encres** | les sous-totaux par type d'encre se somment **BRUTS** ; l'arrondi ne tombe qu'**une fois, sur le total** | 1 |
| **P3 Outillage** | les clichés sont arrondis · l'outil est arrondi (**après** le facteur forme spéciale, s'il s'applique) · **puis leur somme est ré-arrondie** | 3 |
| **P4 Calage** | sur le forfait (sans effet : il est déjà à 2 décimales) | 1 |
| **P5 Roulage** | une seule fois, sur `temps × prix horaire` | 1 |
| **P6 Finitions** | la **base est arrondie**, **puis** `base + forfaits ST` est ré-arrondi | 2 |
| **P7 Main d'œuvre** | une seule fois, sur `heures × prix horaire` | 1 |
| **Coût de revient** | `arrondi( Σ des 7 postes )` | 1 |
| **Prix de vente** | `arrondi( coût_de_revient_déjà_arrondi × (1 + marge) )` — **double arrondi** | 1 |
| **Prix au mille** | `arrondi( prix_vente × 1000 / nb_étiquettes )` | 1 |
| **Multi-lots, par lot** | si le calage est dédupliqué : `arrondi( (revient − calage) × (1 + marge) )` | 1 |
| **Multi-lots, totaux** | `arrondi( Σ des prix de lot **déjà arrondis** )` | 1 |

### ⚠️ Le mode d'arrondi n'est pas le même partout

C'est le piège le plus coûteux, parce qu'il est invisible :

| Emplacement | Mode |
| --- | --- |
| **Tout le moteur de coûts** (les 7 postes, l'agrégation, le prix de vente) | **arrondi au pair le plus proche** — le défaut du type décimal |
| **Le total du devis** | **arrondi au supérieur à la moitié**, demandé explicitement |
| Le matcher de cylindres, sur une division entière | **troncature vers le bas** |

Deux modes différents cohabitent donc sur la même chaîne. Sur une valeur
exactement à mi-chemin — 0,125 par exemple — l'un rend 0,12 et l'autre 0,13.
**À reproduire tel quel**, y compris cette divergence.

### Les deux incohérences assumées

1. **P2 et P3 ne se comportent pas pareil** alors qu'ils font la même chose
   (sommer des sous-totaux) : P2 somme brut et arrondit une fois, P3 arrondit
   chaque part **puis** ré-arrondit la somme.
2. **P6 arrondit sa base avant d'ajouter un forfait**, ce que ne fait aucun autre
   poste.

Elles sont **dans les montants dorés**. Les corriger, c'est manquer les dorés.

## 4. Les sept postes — formules exactes

### P1 — Matière

```
si laize_papier_mm fournie :  laize_facturee_mm = laize_papier_mm
sinon (rétro-compat)       :  laize_facturee_mm = laize_utile_mm + marge_confort_roulage_mm
surface_support_m2 = laize_facturee_mm / 1000 × ml_total
poids_kg           = surface_support_m2 × grammage_g_m2 / 1000
prix_kg            = prix_m2_eur × 1000 / grammage_g_m2
cout               = arrondi_2déc( poids_kg × prix_kg )
```

**Le point métier** : quand la laize papier est fournie, la marge de confort
**n'est plus ajoutée** — elle double-comptait les bords.

L'ancien code gardait un repli `prix_kg` par tarif global, jamais emprunté en
pratique. **Ne pas le reconduire** : un repli jamais exécuté est un repli jamais
testé.

### P2 — Encres

```
surface_imprimee_m2 = laize_utile_mm / 1000 × ml_total
pour chaque (type_encre, nb_couleurs) :
    conso_kg     = surface_imprimee_m2 × nb_couleurs × ratio_g_m2_couleur / 1000
    cout_partiel = conso_kg × prix_kg_du_type
cout = Σ cout_partiel
```

Un type d'encre sans tarif lève une **erreur explicite** — pas de zéro silencieux.

⚠️ **Deux surfaces différentes, et ce n'est pas une incohérence** : P1 facture la
**laize support**, P2 et P6 la **laize utile** (imprimée). La marge de confort est
consommée par le support mais ne reçoit ni encre ni finition.

### P3 — Outillage / Clichés

```
3a clichés : nb_couleurs_total × cliche_prix_couleur_eur
3b outil   : si outil existant -> 0 €      (amorti, pas de re-facturation)
             sinon cout_base = outil_base_eur + nb_traces × outil_par_trace_eur
                   si forme spéciale -> cout_base × surcout_forme_speciale_facteur
cout = 3a + 3b
```

Contrôles arithmétiques avec le **jeu doré** (250 / 60 / ×1,50) :
existant → 0 € · neuf 1 tracé simple → 310 € · neuf 4 tracés simple → 490 € ·
neuf 4 tracés forme spéciale → 735 €.

L'identifiant de l'outil **n'entre pas** dans le calcul : il ne sert qu'à tracer.

### P4 — Mise en route / Calage

```
cout = calage_forfait_eur × nb_calages
```

**Invariant** : `nb_calages = 1 + nb_changements`. Le calage est lié à l'**OUTIL**
(plaque + clichés), **pas à la bobine** — un lot qui réutilise le même montage ne
rajoute **pas** de calage. Le flag `changement_outil_cliche` est porté **par lot**,
et le lot 1 ne le porte jamais : son calage est inclus.

### P5 — Roulage (machine)

```
temps_production_h = ml_total / machine.vitesse_moyenne_m_h
cout               = temps_production_h × cout_exploitation_machine_eur_h
```

`vitesse_moyenne_m_h` est le **seul driver de vitesse** — la vitesse maximale reste
un argument catalogue, jamais un intrant de calcul. Vitesse nulle ou négative →
erreur explicite, jamais de repli silencieux.

### P6 — Finitions

```
surface_imprimee_m2 = laize_utile_mm / 1000 × ml_total
cout = surface_imprimee_m2 × finitions_prix_m2_eur + Σ forfaits de sous-traitance
```

### P7 — Main d'œuvre opérateur

```
heures_calage     = machine.duree_calage_h
heures_production = ml_total / machine.vitesse_moyenne_m_h
heures_total      = heures_calage + heures_production   (ou override du dossier)
cout              = heures_total × cout_operateur_eur_h
```

**Le double-compte P4 / P7 est INTENTIONNEL** et conforme à la pratique flexo :
pendant le calage, deux ressources distinctes sont mobilisées — la **machine
immobilisée** (P4) et l'**humain qui règle** (P7). Ne pas « corriger ».

## 5. Cas de référence V1a — 1 777,00 € HT

**Structure du payload** (les tarifs viennent du jeu doré, pas d'ici) :

```python
DevisInput(
    matiere="Papier Démo 100",
    laize_utile_mm=220,
    laize_papier_mm=Decimal("210"),
    ml_total=3000,
    nb_couleurs_par_type={"process_cmj": 4, "pantone": 1},
    machine="Presse Démo A",
    forfaits_st=[100.00],
)
```

**Décomposition — chaque ligne se recontrôle à la main depuis le § 4 :**

| Poste | Calcul | Montant |
| --- | --- | ---: |
| P1 Matière | 210/1000 × 3000 = 630 m² → × 100/1000 = 63 kg → × 5,00 | **315,00** |
| P2 Encres | 220/1000 × 3000 = 660 m² · quadri 660×4×2/1000 = 5,28 kg × 20,00 = 105,60 · Pantone 1,32 kg × 25,00 = 33,00 | **138,60** |
| P3 Outillage | 5 couleurs × 40,00 = 200,00 · outil existant → 0,00 | **200,00** |
| P4 Calage | forfait 200,00 × 1 calage | **200,00** |
| P5 Roulage | 3000/5000 = 0,6 h × 300,00 | **180,00** |
| P6 Finitions | 660 × 0,2000 = 132,00 + forfait ST 100,00 | **232,00** |
| P7 MO | (2,00 calage + 0,6 production) = 2,6 h × 60,00 | **156,00** |
| | **Coût de revient** | **1 421,60** |
| | × (1 + 0,25) | **1 777,00** |

✅ **Produit par l'ancien moteur avec l'Atelier A, et recontrôlé à la main.**
Ce cas est reproductible depuis ce document seul.

## 5 bis. Cas de référence B — 1 587,66 € HT, celui qui exerce les arrondis

**Structure du payload** — quantités et laizes elles aussi non rondes :

```python
DevisInput(
    matiere="Papier Démo 90",
    laize_utile_mm=213,
    laize_papier_mm=Decimal("197"),
    ml_total=2750,
    nb_couleurs_par_type={"process_cmj": 3, "pantone": 2},
    machine="Presse Démo B",
    forfaits_st=[87.35],
)
```

| Poste | Montant |
| --- | ---: |
| P1 Matière | **231,60** |
| P2 Encres | **129,40** |
| P3 Outillage / Clichés | **189,00** |
| P4 Calage | **193,60** |
| P5 Roulage | **167,12** |
| P6 Finitions | **197,18** |
| P7 MO opérateur | **137,32** |
| **Coût de revient** | **1 245,22** |
| × (1 + 0,275) = 1 587,6555 | **1 587,66** |

### Ce que ce cas verrouille — et qu'un total rond ne verrouille pas

Les valeurs intermédiaires ci-dessous sont **le vrai contenu du test**. Un moteur
réécrit qui arrondit ailleurs, ou dans un autre ordre, produira le même ordre de
grandeur et un centime d'écart.

| Étape | Valeur intermédiaire | Ce qu'elle piège |
| --- | --- | --- |
| P1 `prix_kg` | 4,723756906077348… | **Division non terminante.** Ne jamais arrondir ici. |
| P1 `poids_kg` | 49,028375 | Chaîne de multiplications sans arrondi intermédiaire |
| P2 quadri / Pantone | 3,7780875 kg et 2,518725 kg | Les sous-totaux se somment **bruts** — voir § 3 bis |
| P5 `temps_production_h` | 0,5813953488372093… | Division non terminante, propagée sans arrondi |
| P6 base | 109,828125 → **109,83** | Base arrondie **avant** l'ajout du forfait ST |
| Coût de revient | Σ des postes → **1 245,22** | Le coût de revient est arrondi **avant** la marge |
| Prix de vente | 1 245,22 × 1,275 = 1 587,6555 | **Double arrondi**, et le second mord |

> ⚠️ **Il n'existe pas de règle générale d'arrondi dans ce moteur** — et il ne faut
> pas en inventer une. L'emplacement exact de chaque arrondi est cartographié au
> **§ 3 bis**, poste par poste. Un moteur réécrit qui « nettoie » la règle ne
> retombera pas sur les montants dorés.

## 5 ter. La chaîne de pose — du format d'étiquette au métrage

C'est le cœur du système. Tout ce qui suit est de la **géométrie et de la
convention flexo** : des fonctions pures, sans base de données, et sans une seule
valeur d'atelier.

### Étape 1 — poses en développé (sur le tour de cylindre)

```
pas       = hauteur_etiquette + intervalle_dev_min
nb_poses  = plancher( developpe_cylindre / pas )
intervalle_reel = developpe_cylindre / nb_poses − hauteur_etiquette
si intervalle_reel < intervalle_dev_min :
    nb_poses -= 1  et on recalcule l'intervalle
si nb_poses == 0 : configuration impossible
```

Le repli d'une pose est **volontaire** : on préfère perdre une pose plutôt que de
descendre sous l'intervalle minimum. L'intervalle réel se **redistribue** sur le
tour — il n'est pas figé au minimum.

### Étape 2 — poses en laize (en travers de la bande)

Pour chaque nombre de poses envisagé (« variante ») :

```
espace_dispo = laize_utile − nb_poses_laize × largeur_etiquette
si espace_dispo < 0        : variante impossible
si nb_poses_laize == 1     : intervalle = 0
sinon : intervalle = min( espace_dispo / (nb_poses_laize − 1) , INTERVALLE_LAIZE_MAX )
```

**`INTERVALLE_LAIZE_MAX` = 5 mm**, et c'est une **pratique standard flexo**, pas un
réglage d'atelier : au-delà, ce n'est plus un intervalle utile, c'est de la matière
perdue. On accepte donc des **bords perdus** sur la bobine plutôt qu'une plaque
étirée sur toute la laize.

Un **forçage** de l'intervalle est possible (souveraineté du deviseur) : il
**contourne le plafond** — certains cas particuliers l'exigent — et seule la
faisabilité géométrique est alors vérifiée.

### Étape 3 — largeur de plaque

```
laize_plaque = nb_poses_laize × largeur_etiquette + (nb_poses_laize − 1) × intervalle_laize
```

⚠️ **Ce sont les intervalles INTERNES**, au nombre de `N − 1`. Ce ne sont **pas**
les bords : sur la bobine, les bords sont libres et se traitent à l'étape 4.

### Étape 4 — laize papier commandée au fournisseur

```
laize_mini  = laize_plaque + 2 × bord_lateral
papier      = arrondi_au_palier_superieur( laize_mini , palier_fournisseur )
papier      = min( papier , laize_utile )          ← plafond : la presse rogne
papier      = max( papier , laize_mini_roulable )  ← plancher : contrainte presse
chute_reelle_par_cote = ( papier − laize_plaque ) / 2
```

L'ordre compte : **plafond d'abord, plancher ensuite**. Le `bord_lateral` vient du
barème d'échenillage (§ 7) ou d'une surcharge du deviseur ; le
`palier_fournisseur` traduit le fait que les matières se livrent par paliers
standard. La plaque est posée **centrée** sur la bobine — pas d'asymétrie
gauche/droite.

### Étape 5 — métrage

```
poses_total = nb_poses_dev × nb_poses_laize
nb_tours    = plafond( quantite / poses_total )
ml_total    = nb_tours × developpe_cylindre / 1000
```

**Convention métier : on finit toujours le tour entamé.** D'où le plafond, et non
un arrondi. Une étiquette de plus qu'un multiple exact coûte un tour entier.

### Étape 6 — dérivés

```
m2_consomme = ml_total × laize_papier / 1000
rendement % = ( quantite × largeur × hauteur / 1 000 000 ) / m2_consomme × 100
```

**Diamètre de bobine** — modèle volumique, couches jointives, air négligé :

```
rayon = racine( rayon_mandrin² + ( epaisseur_reelle × ml_total × 1000 ) / π )
diametre = arrondi( 2 × rayon )
```

Les deux inversions de cette formule existent et sont utiles à l'UI : combien
d'étiquettes tiennent dans un diamètre donné, et quel diamètre il faut pour un
nombre d'étiquettes donné. Le **pas** y vaut `hauteur + intervalle_dev`.

⚠️ **Invariant** : l'épaisseur est celle de la **matière réelle**. Une valeur de
repli qui ignorerait la matière est un défaut, pas une commodité.

### Étape 7 — le choix entre configurations

L'optimiseur balaie **cylindres × machines compatibles × variantes de poses**,
écarte les configurations infaisables, cumule des **coefficients multiplicatifs**
(vitesse et gâche), et classe :

```
score = score_du_palier × coef_vitesse_cumulé / coef_gâche_cumulé
```

À palier égal, une configuration plus rapide et moins gâcheuse gagne. Deux règles
de conduite reprises telles quelles :

- **On ne dégrade jamais une contrainte pour remplir le classement.** S'il y a
  moins de candidats que de places, on en retourne moins.
- Les configurations en doublon sont fusionnées avant classement.

## 5 quater. Les 8 sens d'enroulement

Convention flexographique officielle. Trois vues, et une seule est critique :

- **Vue A** — la **planche presse** (verticale, l'avance pointe vers le bas).
- **Vue B** — le rouleau en volume : seule vue où se voit la **face imprimée**
  (dedans / dehors).
- **Vue C** — la **bobine fille déroulée chez le client** (horizontale,
  défilement vers la droite).

**Les paires (1,5) (2,6) (3,7) (4,8) partagent exactement les mêmes rotations en
vues A et C.** Leur seule différence est la face imprimée, visible uniquement en
vue B. C'est le piège classique : un sens « extérieur » et son « intérieur »
correspondant sont indiscernables sur la planche.

| Sens | Libellé officiel | Rotation vue A | Rotation vue C |
| ---: | --- | ---: | ---: |
| 1 | 0° Extérieur droite avant | 90° | 0° |
| 2 | 180° Extérieur gauche avant | 270° | 180° |
| 3 | 270° Extérieur pied avant | 0° | 270° |
| 4 | 90° Extérieur tête avant | 180° | 90° |
| 5 | 0° Intérieur droite avant | 90° | 0° |
| 6 | 180° Intérieur gauche avant | 270° | 180° |
| 7 | 270° Intérieur pied avant | 0° | 270° |
| 8 | 90° Intérieur tête avant | 180° | 90° |

Rotations horaires, en degrés : 0 = tête en haut, 90 = tête à droite,
180 = tête en bas, 270 = tête à gauche.

> ⚠️ **Pourquoi la vue A ne souffre aucune approximation** : c'est elle que lit le
> poseur de clichés pour orienter le cliché sur la presse. Fausse → cliché posé à
> l'envers → **tirage entier à jeter**. Un sens hors de 1–8 lève une erreur ; il
> n'y a pas de valeur par défaut raisonnable.

## 5 quinquies. Le « format approchant » — le cœur de l'argument de vente

Il s'agit de trouver, dans le parc **existant** de l'imprimeur, un outil
quasi compatible plutôt que d'en fabriquer un neuf.

### La formule

Un cylindre magnétique se décrit par son nombre de **dents** `Z`.

```
DENT = 3,175 mm                      (1/8 de pouce — convention industrielle)
pas          = ( Z × DENT ) / nb_etiquettes_par_tour
intervalle   = pas − hauteur_etiquette
```

Le moteur balaie les couples `(Z, nb_etiquettes_par_tour)` et retient ceux qui
satisfont **trois contraintes simultanées** :

1. **Hauteur** : l'intervalle reste entre un minimum et un maximum métier — trop
   faible, le squelette casse ; trop grand, c'est de la matière perdue.
2. **Effet banane** : `Z ≥ développé minimum` pour la largeur de plaque
   considérée (§ 5 sexies).
3. **Laize machine** : `largeur_plaque ≤ laize_max − 2 × marge de sécurité`.

### La stratégie de sélection, qui est le vrai savoir-faire

- **Un seul candidat par `Z`** — celui qui donne le meilleur intervalle pour ce
  cylindre **physique**. Proposer deux configurations du même cylindre n'aide pas
  le deviseur : il n'en a qu'un.
- **Tri par intervalle croissant** : le plus serré des intervalles acceptables
  donne le meilleur **prix au mille**.
- **Top 3**, et **moins de 3 s'il y a moins de candidats viables**. On ne dégrade
  **jamais** une contrainte pour remplir la liste.
- Quand **aucun** cylindre du parc ne convient, on propose explicitement l'option
  « fabriquer un outil neuf », chiffrée — c'est l'alternative, pas un échec.

Les bornes (intervalle mini et maxi, marge de sécurité en laize, plages de `Z` et
de nombre d'étiquettes par tour) sont des **paramètres**, à re-sourcer depuis les
catalogues publics des fabricants de cylindres et à confirmer à la calibration.

## 5 sexies. La structure des quatre barèmes

Les barèmes sont **réglés sur un parc de presses**. Leurs **courbes** ne se
livrent donc pas : on livre la **structure** et un **mode neutre**, puis on
calibre chez l'imprimeur.

Un barème est une entrée typée portant : un **type**, un nom, une liste
optionnelle de **machines auxquelles il s'applique**, ses **données** (JSON), des
notes, et un drapeau d'activité.

| Barème | Nature | Structure des données |
| --- | --- | --- |
| **Effet banane** | **Filtre dur** — appliqué **en premier** | Paliers triés par `largeur_max_mm` → `developpe_mini_mm`. Un cylindre exclu l'est définitivement. |
| **Échenillage** | **Score + coefficients** — ne filtre jamais | Paliers triés par `intervalle_max_mm` → `qualite`, `coef_vitesse`, `coef_gache`, `score`. On prend le **premier** palier dont le maximum couvre l'intervalle. |
| **Confort de roulage** | Coefficients | Structure différente : un sous-barème par **rayon d'angle** (`rayon_max_mm` → coefficient), plus un coefficient **forme courbe** et un coefficient **quinconce**. |
| **Compensation laize/dev** | **Bonus** | Paliers par intervalle en développé → intervalle en laize souhaitable (valeur fixe, ou **pourcentage du développé** au-delà d'un seuil) et coefficient de vitesse amélioré s'il est atteint. |

### Ce que chaque barème encode, en clair

- **Effet banane** : plus la plaque est large, plus le cylindre doit avoir un
  développé important, sinon la plaque se courbe en arc sous la pression et
  dégrade impression et découpe. **La courbe est empirique et non linéaire** —
  elle comporte un saut à un seuil physique de rigidité. Elle ne s'extrapole pas
  par formule : elle se mesure.
- **Échenillage** — le squelette de matière qui reste entre les étiquettes après
  découpe. Intervalle trop faible → squelette fragile → casse à grande vitesse,
  donc ralentissement. Intervalle modéré → optimal. Intervalle large → squelette
  robuste mais gâche inutile, **et impact vitesse paradoxal** : la machine gère
  plus de matière entre poses.
- **Confort de roulage** — un outil en rotation subit la physique d'une roue qui
  aborde un trottoir : plus les angles d'attaque sont vifs, plus chaque tour
  génère un choc qui force à ralentir et use l'outil. Deux facteurs indépendants
  qui se **cumulent multiplicativement** : le rayon des angles (une forme ronde ou
  ovale a son propre coefficient, indépendant du rayon) et la disposition —
  alignée ou en quinconce.
  **Le quinconce est invisible pour le client final** : l'imprimeur peut
  l'activer librement, sans accord.
- **Compensation laize/dev** — quand un intervalle en développé trop grand est
  subi (cylindre non idéal), on **élargit l'intervalle en laize** pour consolider
  le squelette par de la matière transverse. On perd potentiellement une pose en
  laize et on récupère de la vitesse : c'est un arbitrage, tranché par
  l'orchestrateur.

### Mode neutre — ce qui est livré

Un barème vide rend un **palier neutre** : coefficients à **1,0**, qualité
« inconnu », score 0. **Aucun cylindre n'est alors favorisé arbitrairement.**
C'est exactement le comportement voulu à l'installation : l'application calcule,
sans prétendre connaître un parc qu'elle n'a pas encore vu.

### Une cinquième règle, qui n'est pas un barème

**La contrainte client** : la machine de pose du client a sa propre exigence
d'intervalle — sa cellule photoélectrique doit distinguer chaque étiquette. Si
l'écart est trop faible, elle en confond deux et la pose rate.

```
intervalle_dev_min_appliqué = MAX( minimum imprimeur , minimum client )
```

Et quand c'est la contrainte **client** qui l'emporte, on le **dit** : le devis
peut mentionner « intervalle requis par votre machine de pose », ce qui préempte
la question « pourquoi n'avez-vous pas optimisé davantage ? ».

## 5 septies. Le modèle de données du noyau devis

Mono-tenant : **aucune colonne de portée**, aucun scope, aucun module activable.

| Entité | Rôle | Champs structurants |
| --- | --- | --- |
| **Machine** | **Table unique**, source de vérité du parc | laize utile, laize maximale, **vitesse moyenne (seul driver de vitesse)**, durée de calage, nombre de groupes couleurs, modules spéciaux, diamètre maximal de bobine, temps de changement de bobine |
| **Cylindre magnétique** | Le parc d'outils | développé, repère machine, **nombre de porte-clichés disponibles par presse**, date d'inventaire, actif |
| **Outil de découpe** | Formes existantes | format (largeur × hauteur), nombre de poses en laize et en développé, **forme spéciale** (drapeau) |
| **Matière** | Support | grammage, prix au m², **épaisseur réelle** (jamais un défaut qui ignore la matière) |
| **Option de fabrication** | Catalogue des options | ressources requises (groupes couleurs, modules) → **filtre dur** · impacts production (**coefficients de vitesse et de gâche**, temps de calage ajouté) → cumulés **multiplicativement** · tarification (forfait, au m², ou au mille) · drapeau **silhouette automatique** |
| **Paramètres de coûts** | Ce que la calibration produit | cf. § 2 — **vide à l'installation**, sauf la marge |
| **Barème** | Les 4 courbes | type, machines concernées, données JSON, actif |
| **Client** | | + sa **contrainte d'intervalle** de machine de pose |
| **Devis** et **Lot de production** | | le lot porte : cylindre, machine, matière, poses en laize et en développé, sens d'enroulement, quantité, et **`changement_outil_cliche`** |

### La règle silhouette

Certaines options — microperforation, prédécoupe, pose mixte — portent un drapeau
**silhouette automatique**. Il déclenche le calcul silhouette, qui **oriente la
recherche de format** : dès que la forme n'est plus un simple rectangle à rayons
standard, les contraintes d'outil et de confort de roulage changent de régime.

## 6. Cas de référence multi-lots — et la règle du calage

Ces trois cas passent par le **chemin multi-lots** (création de devis complète),
pas par un appel direct au moteur de coûts. Ils vérifient donc aussi la chaîne de
pose et l'agrégation des lots.

**Fixture commune** — Atelier Démo A, plus :

| Élément | Valeur dorée |
| --- | --- |
| Presse | `laize_utile` = **320 mm** · vitesse 5 000 m/h · calage 2,00 h |
| Cylindre | développé = **300 mm** |
| Matière | « Papier Démo 100 » — 100 g/m², 0,50 €/m² |
| Étiquette | 100 × 80 mm |
| Poses | 3 en laize × 2 en développé |
| Quantité | 10 000 par lot |
| Couleurs | **aucune** — volontairement : le poste Encres vaut 0 €, le cas reste déterministe |
| Marge | celle des paramètres, sans surcharge |

### Les trois montants dorés

| Cas | Scénario | Prix de vente HT |
| --- | --- | ---: |
| **M1** | un seul lot | **775,74 €** *(coût de revient 620,59)* |
| **M2** | deux lots, **même montage** (`changement_outil_cliche` faux) | **1 301,48 €** |
| **M3** | deux lots, lot 2 avec **changement d'outil** | **1 551,48 €** |

### Les trois invariants que ces montants verrouillent

1. **`M3 − M2 = 250,00 €`** — exactement **un calage × (1 + marge)** :
   200,00 × 1,25. Le delta ne dépend d'aucun autre poste.
2. **`M2 = M1 + (M1 − 250,00)`** = 775,74 + 525,74. Le second lot du même montage
   coûte le premier **moins son calage** : la déduplication est bien du calage, et
   de rien d'autre.
3. **`M3 = 2 × M1`** = 1 551,48. Deux lots à montage distinct valent exactement
   deux fois le lot seul.

Ces trois égalités se vérifient **sans recalculer un seul poste**. Elles doivent
être écrites en test à côté des montants : un moteur qui tombe sur les trois
nombres mais viole une égalité a un problème ailleurs.

### La chaîne de laize, sur ce cas précis

```
plaque = 3 × 100 + (3 − 1) × intervalle_laize        intervalle plafonné à 5 mm
       = 310 mm
papier = arrondi_palier_sup( 310 + 2 × bord )  puis  min( … , laize_utile 320 )
```

**Le plafond mord** : le brut arrondi dépasse la laize utile, la presse rogne le
bord, et c'est **320 mm** qui est facturé. C'est le cœur de ce cas de référence —
le détail des étapes est au § 5 ter.

### Le détail par lot — à figer au même titre que les totaux

Un total juste avec un détail faux reste un devis que le deviseur ne peut pas
défendre. **Le détail par lot fait donc partie du jeu doré**, et se fige en test.

| Cas | Lot | Prix de vente HT | Coût de revient | Calage dédupliqué |
| --- | ---: | ---: | ---: | ---: |
| **M1** | 1 | 775,74 | 620,59 | 0,00 |
| **M2** | 1 | 775,74 | 620,59 | 0,00 |
| **M2** | 2 | **525,74** | **420,59** | **200,00** |
| **M3** | 1 | 775,74 | 620,59 | 0,00 |
| **M3** | 2 | 775,74 | 620,59 | 0,00 |

**Le détail somme au total** : 775,74 + 525,74 = 1 301,48. C'est vrai **par
construction** — le total est la somme des prix de lot déjà arrondis (§ 3 bis),
et non un calcul parallèle. Cette propriété est elle-même à écrire en test :
`Σ(prix de lot) == total`, sur les trois cas.

**Une trace d'audit accompagne la déduplication** : chaque lot porte le montant de
calage mutualisé (`0,00` ou `200,00`). C'est ce qui permet d'expliquer au client
pourquoi son deuxième lot coûte moins cher que le premier — un argument
commercial, pas seulement une ligne de calcul.

> **Erratum du 20/08/2026.** Une lecture antérieure concluait que le détail par lot
> ne sommait pas au total, et proposait de « corriger » ce point dans la
> réécriture. **C'était une erreur de lecture** : le champ consulté était le calcul
> brut du lot conservé pour audit, et non le prix du lot. L'ancien moteur
> déduplique déjà correctement. Il n'y a **aucun écart volontaire** à protéger —
> seulement des valeurs à reproduire.

## 7. État de la porte G0

**La question** : cette spec suffit-elle à écrire le moteur **sans rouvrir
l'ancien dépôt**, et **sans un seul chiffre d'atelier réel** dedans ?

### ✅ Ce qui est extrait

- [x] Les **formules** des 7 postes, et **où chaque paramètre se lit** (§ 4)
- [x] La **chaîne de pose** complète, en 7 étapes (§ 5 ter)
- [x] La **règle du bord** et le **plafonnement** à la laize utile (§ 5 ter)
- [x] Les **8 sens d'enroulement**, table complète (§ 5 quater)
- [x] Le **« format approchant »** — formule, contraintes, stratégie (§ 5 quinquies)
- [x] La **structure des 4 barèmes** et le mode neutre (§ 5 sexies)
- [x] La **règle silhouette** et le **modèle de données** (§ 5 septies)
- [x] **Cinq montants dorés** : deux mono-lot (§ 5, § 5 bis) et trois multi-lots
      avec la règle du calage (§ 6)
- [x] La **convention de marge** — marge sur coût, pas taux de marque (§ 3)
- [x] L'**ordre des arrondis**, verrouillé par l'Atelier B (§ 5 bis)

### Ce qui reste, et qui n'est pas un blocage

- [ ] **Les développés standard de cylindres** (pas de 3,175 mm — 1/8 de pouce).
      C'est un **catalogue à re-sourcer** depuis la documentation publique des
      fabricants, pas une règle à extraire. Le moteur s'écrit sans, la calibration
      les charge.
- [ ] **Les courbes des 4 barèmes** : elles ne se reprennent pas, **par
      construction**. On livre le mode neutre, et la calibration les fait produire
      chez l'imprimeur.

### Verdict

**G0 est franchie.** Le moteur du lot 1 peut s'écrire à partir de ce document
seul, en TDD, contre les cinq montants dorés et les trois invariants de calage.

## 8. Questions ouvertes pour Eric

1. **Le jeu doré du § 2 est-il validé ?** Il produit 1 777,00 € sur V1a — rond, ce
   qui est plutôt bon signe pour un jeu de référence. Aucune de ses valeurs ne
   coïncide avec un paramètre de l'atelier historique.
2. **Nommage des fixtures** : « Presse Démo A » et « Papier Démo 100 » plutôt que
   des marques réelles. Les catalogues de cylindres et de matières seront
   re-sourcés depuis la documentation publique des fabricants, décrits
   génériquement.
