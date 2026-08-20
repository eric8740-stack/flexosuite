# Contrat d'API — v1

> **Ce document fait loi entre le backend et le front.** CC2 code contre lui ;
> CC1 le met à jour **avant** de changer quoi que ce soit, et **livre le backend
> en premier**. L'inverse envoie le front en 422 — la leçon est déjà payée.
>
> **Chaque section porte son état de livraison** — voir le tableau ci-dessous.
> Un endpoint « spécifié, pas encore livré » répond **404** : il ne répond pas
> « presque », et le front ne doit pas coder comme s'il existait.
>
> Source de vérité métier : `docs/SPEC-METIER.md`. Si les deux divergent, c'est
> la spec qui a raison et ce fichier qui est à corriger.

## État de livraison, section par section

| Section | État au 20/08/2026 |
| --- | --- |
| 1. Service — `GET /api/sante` | ✅ **livré** |
| 1. Service — `GET /api/contexte` | ✅ **livré** — les quatre champs |
| 1 bis. Installation et session | ✅ **livré** — lot 2a |
| 2. Optimisation de pose | ⏳ spécifié, **pas encore livré** |
| 3. Chiffrage | ⏳ spécifié, **pas encore livré** — le moteur existe et est testé, l'endpoint non |
| 4. Devis | ⏳ spécifié, **pas encore livré** |
| 5. Référentiels | ⏳ spécifié, **pas encore livré** |
| 6. Paramètres et calibration | ⏳ spécifié, **pas encore livré** |

> ⚠️ **Un état de livraison faux est pire qu'une absence d'état** : il envoie le
> front coder contre du vide en croyant l'endpoint disponible. Cette table est
> mise à jour **dans la PR qui livre**, jamais après coup.

## 📣 Journal des changements — à lire avant de coder

### v1.1 — 20/08/2026, **livrée** avec le lot 2a

> **Le backend est parti en premier**, comme annoncé. Ce qui suit était déjà
> décrit en v1 : c'est la livraison, pas un changement de forme. Les seules
> nouveautés sont des **précisions** — aucune ne casse ce que CC2 a écrit.

**Ce qui est maintenant réel** (avant : 404 ou champ absent) :

| Endpoint | Ce qui change pour le front |
| --- | --- |
| `GET /api/contexte` | Renvoie les **quatre** champs. `installation_faite` et `calibration_faite` sont exploitables. |
| `POST /api/installation` | Existe. `201`, session ouverte dans la foulée. |
| `POST /api/auth/connexion` · `POST /api/auth/deconnexion` · `GET /api/auth/moi` | Existent. |

**Précisions ajoutées** — elles n'étaient pas écrites, elles le sont :

| Point | Précision |
| --- | --- |
| Corps de réponse de `/api/installation`, `/api/auth/connexion` et `/api/auth/moi` | `{ "identifiant": "...", "role": "administrateur" }` — le **même objet** que `contexte.utilisateur`. Une seule forme d'utilisateur à écrire côté front. |
| Longueur du mot de passe | **8 caractères au minimum**. En dessous : `422 payload_invalide`. Volontairement bas — c'est un poste d'atelier sur réseau local, et une exigence de complexité produit surtout des mots de passe sur un post-it. |
| `POST /api/auth/deconnexion` sans session | Répond **`204`**, pas `401`. Renvoyer une erreur à quelqu'un qui veut partir n'a aucun sens. |
| Requête d'écriture **sans en-tête `Origin`** | **Acceptée.** Tout navigateur en envoie un sur une écriture, y compris cross-site : une requête sans `Origin` ne vient pas d'un navigateur, donc aucun cookie n'est transporté à l'insu de l'utilisateur. Refuser casserait les scripts du package sans rien protéger de plus. |
| `404` sur une **route inconnue** | Sort au format du contrat, `code: "introuvable"`. Aucune réponse d'erreur n'échappe à `{code, detail}` — sinon le front devrait écrire un cas particulier, et c'est ce cas particulier qui finirait par diverger. |
| `calibration_faite` | Vrai quand **les neuf** paramètres de coûts sont renseignés. Au sortir de l'installation il vaut **faux** : l'application se livre à zéro tarif. |

**Ce que CC2 peut débloquer maintenant** : l'écran d'installation, la connexion,
la redirection au `401` et l'aiguillage sur `installation_faite` /
`calibration_faite`. Ils étaient volontairement non figés — ils peuvent l'être.

**Ce qui reste en 404** : optimisation, chiffrage, devis, référentiels,
calibration. Leur forme est spécifiée, elle ne bouge pas ; ils arrivent aux
lots 2b et 2c, **annoncés avant écriture** comme celui-ci.

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
| **Toute erreur porte un `code` stable** | ⚠️ **CASSANT si le front lit `detail`** | Le corps devient `{"code": ..., "detail": ...}`. Le front aiguille sur `code`, **jamais** sur le texte : un message destiné à être lu se reformule, et un aiguillage bâti dessus casse en silence. |
| **Cookie de session figé** | additif | `SameSite=Strict`, `HttpOnly`, `Secure` en **réglage**, expiration absolue de 12 h, révocation côté serveur. ⚠️ En développement, front et backend doivent employer **le même nom d'hôte** — `127.0.0.1` et `localhost` sont cross-site. |
| **Contrôle d'origine sur les écritures** | additif | `POST`/`PUT`/`DELETE` refusés en **403 `origine_refusee`** si l'`Origin` n'est pas celle du service. |
| **Partage d'origine réservé au développement** | ✅ **déjà livré** | Le middleware n'est monté **que** si des origines sont explicitement listées. Absent du package Windows et de la démo, qui sont mono-port. |
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
| **Erreurs** | `{"code": "...", "detail": "..."}` — **toujours les deux**. Voir ci-dessous. |
| **Codes HTTP** | 200 lecture · 201 création · 204 suppression · 400 règle métier violée · **401 session absente ou expirée** · **403 interdit** · 404 inconnu · 409 conflit d'état · 422 payload invalide. |
| **Mode démo** | Quand il est actif, toute écriture répond **403** `mode_demo_lecture_seule`. |

### Le format d'erreur — deux champs, et ils ont deux publics

```json
{ "code": "installation_requise", "detail": "Aucun compte n'existe encore." }
```

| Champ | Pour qui | Règle |
| --- | --- | --- |
| `code` | **la machine** | Identifiant **stable**, en minuscules avec tirets bas. Il ne change jamais sans passer par le journal des changements. |
| `detail` | **l'humain** | Phrase en français, **affichable telle quelle** à un deviseur. Aucune trace technique. Peut être reformulée à tout moment. |

> ⚠️ **Le front ne décide jamais à partir de `detail`.** Un texte destiné à être
> lu se reformule ; un aiguillage bâti dessus casse à la première relecture, et
> il casse **en silence**. Toutes les erreurs que le front doit distinguer
> portent un `code` — pas seulement le 409, sinon le front gérerait deux formes.

**Les codes de la v1** — tout ajout passe par le journal des changements :

| `code` | HTTP | Ce que le front doit faire |
| --- | ---: | --- |
| `session_absente` | 401 | Rediriger vers la connexion, **sans perdre la saisie en cours** |
| `identifiants_invalides` | 401 | Rester sur la connexion, message générique |
| `installation_requise` | 409 | Envoyer vers l'assistant d'installation |
| `installation_deja_faite` | 409 | L'assistant ne se rejoue pas : renvoyer vers la connexion |
| `calibration_requise` | 409 | Envoyer vers l'assistant de calibration |
| `mode_demo_lecture_seule` | 403 | Expliquer que la démo est en lecture seule |
| `origine_refusee` | 403 | Ne pas réessayer : c'est une écriture rejetée par sécurité |
| `introuvable` | 404 | Message d'absence, pas de réessai |
| `payload_invalide` | 422 | Signaler les champs fautifs |
| `regle_metier` | 400 | Afficher `detail` tel quel — c'est du métier, pas une panne |

## 1. Service — ✅ livré

### `GET /api/sante`

```json
{ "statut": "ok", "application": "FlexoSuite" }
```

### `GET /api/contexte` — ✅ livré

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

## 1 bis. Installation et session — ✅ livré (lot 2a)

Repris du patron de livraison locale : **hachage du mot de passe et révocation
de session**, pas de jeton réinventé.

### `POST /api/installation`

Premier démarrage, **une seule fois**. Crée le compte administrateur.

```json
{ "identifiant": "atelier", "mot_de_passe": "..." }
```

Le mot de passe fait **8 caractères au minimum** ; en dessous,
`422 payload_invalide`.

`201`, corps `{ "identifiant": "...", "role": "administrateur" }`, et une session
ouverte dans la foulée — faire ressaisir le mot de passe qu'on vient de choisir
n'apporterait rien. Si un compte existe déjà : **409** — l'assistant ne se
rejoue pas, sinon il deviendrait une porte d'entrée.

L'installation crée aussi la ligne de paramètres de coûts, **vide de tarifs**,
avec la seule marge. `calibration_faite` vaut donc **faux** juste après.

> Le mot de passe n'est stocké que **haché**. C'est pour cela que le package
> livre `reinitialiser-mot-de-passe.bat` : sans lui, un mot de passe perdu
> bloquerait l'imprimerie.

### `POST /api/auth/connexion`

```json
{ "identifiant": "atelier", "mot_de_passe": "..." }
```

`200`, corps `{ "identifiant": "...", "role": "administrateur" }` — **le même
objet** que `contexte.utilisateur` — et cookie de session **HttpOnly**. Le front
ne lit jamais le jeton : il n'en a pas besoin, et ne pas pouvoir le lire est
précisément la protection.

Identifiants faux → **401**, avec un message volontairement **indifférencié** :
on ne dit pas si c'est l'identifiant ou le mot de passe qui est faux.

### Le cookie de session — figé ici, pas laissé à l'implémentation

| Attribut | Valeur | Pourquoi |
| --- | --- | --- |
| Nom | `flexosuite_session` | — |
| `HttpOnly` | **oui**, toujours | Le front ne lit jamais le jeton. Ne pas pouvoir le lire **est** la protection. |
| `SameSite` | **`Strict`** | Voir la note ci-dessous : il **ne casse pas** le développement. |
| `Secure` | **réglage**, pas constante | `true` sur la démo publique (HTTPS). `false` pour le package client, qui tourne en **HTTP** sur le réseau de l'imprimerie et serait sinon inutilisable. **Défaut : `true`** — la dérogation est explicite, jamais implicite. |
| `Path` | `/` | Un seul port sert la page et l'API. |
| Durée | **12 h**, expiration **absolue** | Réglable. Pas de prolongation glissante : une session oubliée sur un poste d'atelier finit par expirer, quoi qu'il arrive. |
| Révocation | **côté serveur** | La déconnexion invalide la session en base, elle ne se contente pas d'effacer le cookie. Un cookie effacé sur un poste ne protège rien si le jeton reste valide. |

> **`SameSite=Strict` ne casse pas le développement**, contrairement à l'intuition.
> Le **port n'entre pas** dans la définition de *same-site* : `localhost:3000` et
> `localhost:8000` sont bien same-site.
>
> ⚠️ **En revanche l'hôte, lui, compte** : `127.0.0.1` et `localhost` sont deux
> hôtes **différents**, donc cross-site. En développement, front et backend
> doivent employer **le même nom d'hôte** — les deux sur `localhost`, ou les deux
> sur `127.0.0.1`. Les mélanger produit une session qui « ne tient pas », sans
> aucun message d'erreur.

### Contrôle d'origine sur toute écriture

Toute requête **`POST`, `PUT`, `DELETE`** est refusée si son en-tête `Origin`
n'est pas celle du service — **403 `origine_refusee`**.

`SameSite=Strict` couvre déjà l'essentiel ; ce contrôle est la **deuxième
serrure**, celle qui tient si un navigateur ancien ou une extension traite
`SameSite` avec largesse. Les lectures ne sont pas concernées : elles ne
modifient rien.

En développement avec deux ports, les origines acceptées sont celles listées
dans le réglage de partage d'origine — **la même liste**, pour qu'il n'y ait pas
deux endroits où se tromper. L'origine du service elle-même est toujours
acceptée, sans avoir à être listée.

> **Une écriture sans en-tête `Origin` est acceptée**, et c'est délibéré. Tout
> navigateur en envoie un sur une méthode d'écriture, y compris pour un
> formulaire cross-site : une requête sans `Origin` ne vient donc pas d'un
> navigateur, et sans navigateur il n'y a pas de cookie transporté à l'insu de
> l'utilisateur. Refuser casserait les scripts du package et les tests sans
> rien protéger de plus.

### `POST /api/auth/deconnexion`

`204`, session **révoquée côté serveur** — pas seulement le cookie effacé.

Sans session valide, la réponse reste **`204`**. Renvoyer une erreur à quelqu'un
qui veut partir n'a aucun sens.

### `GET /api/auth/moi`

`200` avec `{ "identifiant": "...", "role": "administrateur" }`, `401` sinon.

### Ce que le front doit faire d'un 401

Un 401 peut survenir **à tout moment** : une session expire pendant une saisie.
La règle : **rediriger vers la connexion sans perdre le travail en cours**, et
revenir sur l'écran quitté après reconnexion. Un devis à demi saisi qui
disparaît parce qu'une session a expiré est une perte sèche pour le deviseur.

## 2. Optimisation de pose — le point d'entrée unique — ⏳ pas encore livré

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

## 3. Chiffrage — ⏳ pas encore livré

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

## 4. Devis — ⏳ pas encore livré

| Verbe | Route | Effet |
| --- | --- | --- |
| `POST` | `/api/devis` | Crée le devis et ses lots. `201`. |
| `GET` | `/api/devis` | Liste paginée : `{ "elements": [...], "total": n }`, paramètres `page` (1 par défaut) et `taille` (25 par défaut, 200 au plus). |
| `GET` | `/api/devis/{id}` | Le devis avec ses lots. |
| `PUT` | `/api/devis/{id}` | Remplace le devis et ses lots. |
| `DELETE` | `/api/devis/{id}` | `204`. |

Le devis porte un **numéro attribué par le serveur** — le front ne le fabrique
jamais. Statuts : `brouillon`, `envoye`, `accepte`, `refuse`.

## 5. Référentiels — ⏳ pas encore livré

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

## 6. Paramètres et calibration — ⏳ pas encore livré

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
