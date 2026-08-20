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
> Les paramètres de ce document sont un **jeu doré fabriqué** — rond, arbitraire
> et manifestement fictif.
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

1. On choisit un **jeu de paramètres rond et manifestement fictif** (§ 2).
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

## 2. Le jeu doré — « Atelier Démo »

Entièrement fictif. Tout est rond, précisément pour qu'on voie qu'il l'est.
C'est aussi le jeu de la **démo publique**.

### Paramètres de coûts

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

### Données de référence

| Objet | Valeur dorée |
| --- | --- |
| Matière « Papier Démo 100 » | 100 g/m², 0,50 €/m² → **5,00 €/kg** |
| Presse « Presse Démo A » | `vitesse_moyenne_m_h` = 5 000 · `duree_calage_h` = 2,00 |
| Encre quadri | 20,00 €/kg · ratio 2,000 g/m²/couleur |
| Encre Pantone | 25,00 €/kg · ratio 2,000 g/m²/couleur |
| Forfait de sous-traitance | 100,00 € |

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
cout_revient  = Σ P1..P7
prix_vente_ht = arrondi_2déc( cout_revient × (1 + marge) )
```

Tous les calculs intermédiaires sont en `Decimal` — **jamais** en flottant.

**Où la marge se lit** (constaté dans l'ancien code, pas supposé) :
`ConfigCouts.marge_standard_pct`, stockée en **pourcentage** (0–100) et convertie
en fraction. **Ni** `Entreprise.pct_marge_defaut`, **ni** une constante de repli —
les deux existaient et ont été retirées. Priorité : override porté par le devis,
sinon paramètres. **Pas de troisième niveau** : sans paramètres, le moteur lève une
erreur explicite plutôt que de fabriquer un prix.

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

✅ **Produit par l'ancien moteur avec le jeu doré, et recontrôlé à la main.**
V1a est reproductible depuis ce document seul.

## 6. Cas de référence P0b et D1 — structure figée, montants à produire

**P0b — chemin multi-lots, un seul lot.** Structure :

```json
{
  "payload_input": {
    "format_etiquette_largeur_mm": 100,
    "format_etiquette_hauteur_mm": 80,
    "mode_calcul": "manuel"
  },
  "quantite_totale": 10000,
  "lots": [{ "nb_poses_dev": 2, "nb_poses_laize": 3,
             "sens_enroulement": 1, "quantite": 10000 }]
}
```

Dépendances de fixture à figer explicitement : presse de laize utile **320 mm** ·
**aucune couleur** dans le payload → **P2 = 0 €**, volontairement, pour rendre le
cas déterministe · pas d'override de marge.

**Le plafond de laize mord ici, et c'est le cœur du cas** : laize plaque
= 3 poses × 100 mm + 2 bords = **310 mm** ; papier brut = **330 mm** ; plafonné à
la laize utile = **320 mm**.

**D1 — le calage suit le montage.** Même fixture, **deux lots identiques** :

| Scénario | `changement_outil_cliche` du lot 2 | Calages attendus |
| --- | --- | ---: |
| D1-a | `False` | **1** (lot 2 dédupliqué) |
| D1-b | `True` | **2** |

Garde de cohérence à écrire en test : `D1-b − D1-a` doit valoir **exactement un
calage × (1 + marge)**, et **D1-a doit contenir le montant de P0b** (le lot 1 seul
est le scénario P0b).

⚠️ **Les montants dorés de P0b et D1 ne sont pas encore produits** : ils passent par
la chaîne de pose, qui n'est pas extraite (§ 7). La règle exacte du bord et du
plafonnement est ici telle que l'ancien code la décrit, **pas telle qu'elle a été
lue**.

## 7. Ce qui n'est PAS encore extrait — la porte G0 reste fermée

Tant que cette liste n'est pas vide, on **n'écrit pas de moteur**.

- [ ] **La chaîne de pose** — comment on passe du format étiquette et du cylindre
      au couple (`nb_poses_laize`, `nb_poses_dev`), puis à `laize_utile`,
      `laize_papier` et `ml_total`. **C'est ce qui manque pour produire les
      montants dorés de P0b et D1.**
- [ ] **La règle du bord** et le **plafonnement à la laize utile** — la chaîne
      exacte qui transforme 3 poses × 100 mm en 310 puis 320 mm.
- [ ] **Les 8 sens d'enroulement** — table de correspondance.
- [ ] **La règle silhouette** : forme ≠ rectangle, rayon hors valeurs standard, ou
      prédécoupe / microperfo / pose mixte → oriente la recherche de format.
- [ ] **Le « format approchant »** — l'argument de vente central, donc la règle la
      plus importante du produit. Sa logique de score reste à extraire.
- [ ] **La structure des 4 barèmes** — échenillage, effet banane, confort de
      roulage, compensation laize/dev. **La forme des courbes, jamais les valeurs**
      d'un parc existant. Livrés en **mode neutre** (coefficient 1,0 = sans effet),
      puis ajustés par calibration.
- [ ] **Les 19 développés standard** (de 72 à 144 mm, pas de 3,175 mm) —
      re-sourcés depuis les **catalogues publics** de fabricants de cylindres.
- [ ] **Le modèle de données du noyau devis**, sans multi-tenant : machines,
      matières, outils, cylindres, clients, devis et lots, paramètres.

## 8. Questions ouvertes pour Eric

1. **Le jeu doré du § 2 est-il validé ?** Il produit 1 777,00 € sur V1a — rond, ce
   qui est plutôt bon signe pour un jeu de référence. Aucune de ses valeurs ne
   coïncide avec un paramètre de l'atelier historique.
2. **Nommage des fixtures** : « Presse Démo A » et « Papier Démo 100 » plutôt que
   des marques réelles. Les catalogues de cylindres et de matières seront
   re-sourcés depuis la documentation publique des fabricants, décrits
   génériquement.
