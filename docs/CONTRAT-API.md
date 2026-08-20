# Contrat d'API — v1

> **Ce document fait loi entre le backend et le front.** CC2 code contre lui ;
> CC1 le met à jour **avant** de changer quoi que ce soit, et **livre le backend
> en premier**. L'inverse envoie le front en 422 — la leçon est déjà payée.
>
> **Ce qui existe aujourd'hui est marqué ✅** ; le reste arrive avec le lot 2.
> Un endpoint absent répond 404, il ne répond pas « presque ».
>
> Source de vérité métier : `docs/SPEC-METIER.md`. Si les deux divergent, c'est
> la spec qui a raison et ce fichier qui est à corriger.

## 📣 Journal des changements — à lire avant de coder

### v1 — annoncée le 20/08/2026, avant écriture du lot 2

> **Un seul changement casse l'existant : l'authentification arrive.** Les
> autres sont additifs. Rien n'est encore implémenté au moment de l'annonce —
> **le backend partira en premier**, et cette section dira quand.

| Changement | Nature | Effet sur le front |
| --- | --- | --- |
| **Authentification sur tous les endpoints de données** | ⚠️ **CASSANT** | Un appel sans session valide reçoit **401**. Tout écran de données doit savoir réagir à un 401 : rediriger vers la connexion, sans perdre la saisie en cours. |
| **Assistant d'installation au premier démarrage** | ⚠️ **CASSANT en pratique** | Tant qu'aucun compte n'existe, les endpoints de données répondent **409** avec `"installation_requise"`. Le front doit envoyer vers l'assistant, **pas** afficher une page vide. |
| **`GET /api/contexte` gagne trois champs** | additif | `installation_faite`, `calibration_faite`, `utilisateur`. Un front qui ignore ces champs continue de fonctionner — mais il affichera un devis calculé sans tarifs. |
| **Endpoints `/api/auth/*` et `/api/installation`** | additif | Nouveaux. |
| **Format d'erreur précisé pour 401 / 403 / 409** | précision | Voir « Erreurs » ci-dessous. |
| **Pagination précisée** | précision | `{"elements": [...], "total": n}`, paramètres `page` et `taille`. |

**Ce que CC2 peut coder dès maintenant, sans risque** : les écrans
d'optimisation et d'aperçu de chiffrage, les référentiels, la mise en page.
Leur forme de réponse **ne bouge pas**.

**Ce qu'il vaut mieux ne pas figer avant la livraison du backend** : la gestion
de session, la redirection au 401, et l'écran d'installation.

### v0 — 20/08/2026

Contrat initial : conventions, optimisation de pose comme point d'entrée unique,
aperçu de chiffrage, devis, référentiels, calibration.

## Conventions, valables partout

| Règle | Détail |
| --- | --- |
| **Préfixe** | Tout est sous `/api`. La racine `/` sert le front. |
| **Origine** | En production, front et API partagent la **même origine** (mono-port). Le front n'écrit **jamais** d'URL absolue. |
| **Montants** | Sérialisés en **chaîne** (`"1777.00"`), jamais en nombre flottant. Le front ne fait **aucun calcul monétaire** : il affiche. |
| **Dimensions** | En **millimètres**, entiers ou décimaux selon le champ. Les longueurs de bande sont en **mètres linéaires**. |
| **Langue** | Champs en **français**. Pas de `company`, pas de `width`. |
| **Dates** | ISO 8601, UTC. |
| **Erreurs** | `{"detail": "..."}` — le message est **affichable tel quel** à un deviseur. Pas de trace technique dans `detail`. |
| **Codes** | 200 lecture · 201 création · 204 suppression · **401 session absente ou expirée** · **403 interdit (mode démo)** · 400 règle métier violée · 404 inconnu · 409 conflit d'état · 422 payload invalide. |
| **Mode démo** | Quand il est actif, toute écriture répond **403** avec un message explicite. |

## 1. Service ✅

### `GET /api/sante`

```json
{ "statut": "ok", "application": "FlexoSuite" }
```

### `GET /api/contexte`

Ce que le front doit savoir **avant d'afficher quoi que ce soit**. Toujours
accessible **sans session** : c'est lui qui dit s'il en faut une.

```json
{
  "mode_demo": false,
  "installation_faite": true,
  "calibration_faite": false,
  "utilisateur": { "identifiant": "atelier", "role": "administrateur" }
}
```

`utilisateur` vaut `null` sans session ouverte.

**Les deux drapeaux commandent l'aiguillage du front, dans cet ordre :**

1. `installation_faite` à **faux** → aucun compte n'existe. Envoyer vers
   l'assistant d'installation. Les endpoints de données répondent **409**.
2. `calibration_faite` à **faux** → l'application est **livrée à zéro tarif**.
   Envoyer vers l'assistant de calibration. Un devis calculé sans tarifs
   n'aurait aucun sens : ne pas proposer d'écran de devis, et surtout ne pas
   afficher de prix à zéro — un prix faux est pire qu'une absence de prix.

## 1 bis. Installation et session

Repris du patron de livraison locale : **hachage du mot de passe et révocation
de session**, pas de jeton réinventé.

### `POST /api/installation`

Premier démarrage, **une seule fois**. Crée le compte administrateur.

```json
{ "identifiant": "atelier", "mot_de_passe": "..." }
```

`201` et une session ouverte dans la foulée. Si un compte existe déjà :
**409** — l'assistant ne se rejoue pas, sinon il deviendrait une porte d'entrée.

> Le mot de passe n'est stocké que **haché**. C'est pour cela que le package
> livre `reinitialiser-mot-de-passe.bat` : sans lui, un mot de passe perdu
> bloquerait l'imprimerie.

### `POST /api/auth/connexion`

```json
{ "identifiant": "atelier", "mot_de_passe": "..." }
```

`200` + cookie de session **HttpOnly**. Le front ne lit jamais le jeton : il
n'en a pas besoin, et ne pas pouvoir le lire est précisément la protection.

Identifiants faux → **401**, avec un message volontairement **indifférencié** :
on ne dit pas si c'est l'identifiant ou le mot de passe qui est faux.

### `POST /api/auth/deconnexion`

`204`, session **révoquée côté serveur** — pas seulement le cookie effacé.

### `GET /api/auth/moi`

`200` avec l'utilisateur courant, `401` sinon.

### Ce que le front doit faire d'un 401

Un 401 peut survenir **à tout moment** : une session expire pendant une saisie.
La règle : **rediriger vers la connexion sans perdre le travail en cours**, et
revenir sur l'écran quitté après reconnexion. Un devis à demi saisi qui
disparaît parce qu'une session a expiré est une perte sèche pour le deviseur.

## 2. Optimisation de pose — le point d'entrée unique

### `POST /api/optimisation/configurations`

Le cœur du produit : à partir d'un brief client, proposer les meilleures
configurations réalisables **avec le parc existant**. C'est le « format
approchant ».

**Requête**

```json
{
  "format": { "largeur_mm": 100, "hauteur_mm": 80 },
  "quantite": 10000,
  "nb_couleurs": 5,
  "matiere_id": 12,
  "contrainte_client": { "intervalle_dev_min_mm": "3.0" },
  "options_codes": ["microperfo"],
  "forcages": {
    "intervalle_laize_mm": null,
    "nb_poses_laize": null,
    "machine_id": null
  }
}
```

`contrainte_client`, `options_codes` et `forcages` sont **facultatifs**. Les
`forcages` traduisent la souveraineté du deviseur : ils **contournent** le
plafond d'intervalle en laize, et seule la faisabilité géométrique est vérifiée.

**Réponse `200`**

```json
{
  "configurations": [
    {
      "id": "cyl12-mach3-3p",
      "rang": 1,
      "cylindre": { "id": 12, "developpe_mm": "300.00", "nb_dents": 94 },
      "machine": { "id": 3, "nom": "Presse Démo A", "laize_utile_mm": "320.00" },
      "poses": { "laize": 3, "developpe": 2, "total": 6 },
      "intervalles_mm": { "laize": "5.00", "developpe": "70.00" },
      "laizes_mm": { "plaque": "310.00", "papier": "320.00", "chute_par_cote": "5.00" },
      "metrage": { "nb_tours": 1667, "ml_total": 501 },
      "rendement_pct": "49.90",
      "score": "82.4",
      "coefficients": { "vitesse": "1.00", "gache": "1.00" },
      "alertes": []
    }
  ],
  "aucun_outil_compatible": false,
  "outil_a_fabriquer": null,
  "alertes": []
}
```

**Règles que le front doit respecter, parce qu'elles sont métier :**

- **Il peut y avoir moins de 3 configurations, et c'est normal.** On ne dégrade
  jamais une contrainte pour remplir la liste. Le front n'invente pas de
  quatrième ligne et n'affiche pas « aucun résultat » s'il en reçoit une seule.
- Quand `aucun_outil_compatible` est vrai, `outil_a_fabriquer` porte la
  proposition chiffrée d'un outil neuf. **C'est une alternative, pas un échec** :
  à présenter comme telle.
- Le **tri est déjà fait** (`rang`). Le front ne re-trie pas.
- `alertes` est une liste de `{ "niveau": "info|attention", "message": "..." }`.
  Les messages sont **rédigés pour un deviseur** et s'affichent tels quels.
- ⚠️ **`ml_total` est un ENTIER de mètres**, pas un décimal. La chaîne comporte
  deux montées successives : le nombre de tours est plafonné (on finit le tour
  entamé), **puis** le métrage est arrondi au mètre supérieur. Ici 1 667 tours
  × 300 mm = 500,10 m → **501**. Le front affiche la valeur reçue, il ne la
  recalcule pas.

### Les 8 sens d'enroulement

Le sens est choisi côté front, entre **1 et 8**. Le backend rend les rotations à
appliquer aux deux vues :

### `GET /api/sens-enroulement`

```json
{
  "sens": [
    { "numero": 1, "libelle": "0° Extérieur droite avant",
      "rotation_vue_planche": 90, "rotation_vue_bobine": 0, "face": "exterieur" }
  ]
}
```

> ⚠️ **Piège à ne pas masquer dans l'UI** : les paires (1,5) (2,6) (3,7) (4,8)
> ont **exactement les mêmes rotations** sur les deux vues. Seule la **face
> imprimée** les distingue. Un affichage qui ne montre que la planche rend ces
> sens indiscernables — et une vue planche fausse, c'est un cliché posé à
> l'envers et un tirage entier à jeter.

## 3. Chiffrage

### `POST /api/devis/apercu`

Chiffrage **sans rien enregistrer**. C'est ce que le front appelle à chaque
modification pour tenir un prix à jour.

**Requête**

```json
{
  "lots": [
    {
      "configuration_id": "cyl12-mach3-3p",
      "matiere_id": 12,
      "quantite": 10000,
      "nb_couleurs_par_type": { "quadri": 4, "pantone": 1 },
      "changement_outil_cliche": false,
      "options_codes": [],
      "forfaits_sous_traitance": [{ "libelle": "Pelliculage", "montant_eur": "100.00" }],
      "outil_existant": true,
      "nb_traces": 1,
      "forme_speciale": false
    }
  ],
  "marge_pct_override": null
}
```

**Réponse `200`**

```json
{
  "postes": [
    { "numero": 1, "libelle": "Matière", "montant_eur": "315.00" },
    { "numero": 2, "libelle": "Encres", "montant_eur": "138.60" },
    { "numero": 3, "libelle": "Outillage / Clichés", "montant_eur": "200.00" },
    { "numero": 4, "libelle": "Mise en route / Calage", "montant_eur": "200.00" },
    { "numero": 5, "libelle": "Roulage", "montant_eur": "180.00" },
    { "numero": 6, "libelle": "Finitions", "montant_eur": "232.00" },
    { "numero": 7, "libelle": "Main d'œuvre opérateur", "montant_eur": "156.00" }
  ],
  "cout_revient_eur": "1421.60",
  "marge_pct": "25.00",
  "coefficient": "1.25",
  "prix_vente_ht_eur": "1777.00",
  "prix_au_mille_eur": "177.70",
  "nb_calages": 1,
  "details_par_lot": [
    {
      "ordre": 0,
      "prix_vente_ht_eur": "1777.00",
      "cout_revient_eur": "1421.60",
      "calage_mutualise_eur": "0.00"
    }
  ],
  "alertes": []
}
```

**Trois obligations pour le front :**

1. **`coefficient` s'affiche à côté de `marge_pct`.** `× (1 + pct)` est une
   **marge sur coût de revient**, pas un taux de marque. Un imprimeur qui lit
   « 30 % » comme un taux de marque attend 1,4286 et facture 9 % en dessous.
   Le pourcentage seul est une information incomplète — le backend fournit le
   coefficient exprès.
2. **`details_par_lot` somme au total**, par construction. Le front peut donc
   afficher le détail sans crainte de contradiction — et **doit** l'afficher :
   un total juste avec un détail muet n'est pas défendable devant un client.
3. **`calage_mutualise_eur`** dit pourquoi un lot coûte moins cher que le
   précédent. C'est un argument commercial, pas une ligne technique : à montrer.

### `GET /api/devis/{id}/apercu`

Même réponse, pour un devis déjà enregistré.

## 4. Devis

| Verbe | Route | Effet |
| --- | --- | --- |
| `POST` | `/api/devis` | Crée le devis et ses lots. `201`. |
| `GET` | `/api/devis` | Liste paginée : `{ "elements": [...], "total": n }`, paramètres `page` (1 par défaut) et `taille` (25 par défaut, 200 au plus). |
| `GET` | `/api/devis/{id}` | Le devis avec ses lots. |
| `PUT` | `/api/devis/{id}` | Remplace le devis et ses lots. |
| `DELETE` | `/api/devis/{id}` | `204`. |

Le devis porte un **numéro attribué par le serveur** — le front ne le fabrique
jamais. Statuts : `brouillon`, `envoye`, `accepte`, `refuse`.

## 5. Référentiels

Même forme pour tous : `GET` liste · `GET /{id}` · `POST` · `PUT /{id}` ·
`DELETE /{id}`.

| Ressource | Route | Champs structurants |
| --- | --- | --- |
| Machines | `/api/machines` | laize utile, laize maxi, **vitesse moyenne (seul driver de vitesse)**, durée de calage, groupes couleurs, modules |
| Cylindres | `/api/cylindres` | développé, nombre de dents, repère machine, porte-clichés disponibles, actif |
| Matières | `/api/matieres` | grammage, prix au m², **épaisseur réelle** |
| Outils de découpe | `/api/outils` | format, poses laize et développé, forme spéciale |
| Clients | `/api/clients` | coordonnées + **contrainte d'intervalle** de sa machine de pose |
| Options | `/api/options` | ressources requises, coefficients vitesse et gâche, tarification, drapeau silhouette |

## 6. Paramètres et calibration

### `GET /api/parametres/couts` · `PUT /api/parametres/couts`

Le `PUT` est **partiel** : seuls les champs envoyés sont modifiés. Un
enregistrement sans modification ne déclenche **aucun appel**.

⚠️ **À l'installation, tous ces champs sont vides** — sauf la marge. C'est
délibéré : livrer les tarifs d'un autre atelier produirait des devis faux.

### `POST /api/calibration/taux-machine`

L'assistant ne demande **jamais un tarif à recopier**, seulement des nombres que
l'imprimeur connaît :

```json
{ "prix_achat_presse_eur": "250000.00", "duree_amortissement_ans": 10,
  "heures_productives_par_an": 1600, "energie_eur_an": "12000.00",
  "maintenance_eur_an": "8000.00" }
```

**Réponse** — le taux **et son explication**, parce qu'un chiffre qu'on ne sait
pas justifier ne sera pas adopté :

```json
{ "taux_eur_h": "27.50",
  "detail": [{ "libelle": "Amortissement", "montant_eur_h": "15.63" }] }
```

### `GET /api/baremes` · `PUT /api/baremes/{type}`

Types : `echenillage`, `effet_banane`, `confort_roulage`, `compensation_laize_dev`.

⚠️ **Livrés en mode neutre** — coefficients à 1,0, aucune configuration
favorisée. Le front doit le **dire** : tant qu'un barème n'est pas calibré, les
scores sont indicatifs.

## Ce qui n'entre pas dans ce contrat

Stock, contrôle qualité de BAT et assistant IA sont **reportés**. Aucun endpoint,
aucun champ, aucun bouton grisé « bientôt » : une promesse dans l'UI est une
dette.
