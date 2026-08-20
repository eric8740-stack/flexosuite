# FlexoSuite — consignes de travail

Application de devis pour imprimeurs flexographiques, **installée chez le
client**. Réécrite depuis zéro le 20/08/2026.

## À lire avant d'agir

1. `docs/REPRISE.md` — l'état **réel** du chantier, et qui tient quoi.
2. `docs/PLAN.md` — les lots et leurs **portes de sortie**.
3. `docs/SPEC-METIER.md` — le cahier de recette : formules, invariants, chaîne
   de pose, et les **montants dorés**.

`git fetch -p` avant tout état git.

## Les trois règles qui ne se discutent pas

### 1. Aucun chiffre d'atelier réel dans ce dépôt

Il est **public**. Les **formules** et les **invariants** se publient — c'est de
la convention professionnelle flexo. Les **valeurs** d'un atelier qui les a
payées, non : ni tarif, ni barème réglé sur un parc de presses, ni nom
d'entreprise, ni en commentaire.

Toute valeur chiffrée de tarif vit dans **un unique module de fixtures
fictives**. `tests/test_confidentialite_livraison.py` le vérifie en CI.

### 2. L'application se livre à zéro tarif

Les tarifs sont produits **chez l'imprimeur** par un assistant de calibration, à
partir de chiffres qu'il connaît. Livrer les tarifs d'un autre atelier
produirait des devis faux. Seule exception : la marge par défaut (30 %),
**confirmée explicitement** à l'installation.

### 3. Les montants dorés ne se retouchent jamais

Ils sortent d'un moteur validé. Un écart d'un centime se **signale** ; il ne se
corrige pas en changeant l'attendu. Re-baseline = **validation explicite
d'Eric**, jamais une décision de session.

Corollaire : **l'arrondi se reproduit, il ne se normalise pas.** La carte des
arrondis, poste par poste, est au § 3 bis de la spec — avec ses incohérences,
qui sont dans les montants dorés. Uniformiser est un chantier séparé.

## Architecture de livraison — imposée, non négociable

- **SQLite**, aucun serveur de base à installer chez le client.
- **Front en export statique**, servi par le backend : **mono-processus,
  mono-port**.
  ⛔ **Jamais** de route API Next, de middleware ni de server action — les trois
  cassent l'export, donc la livraison. La CI les refuse.
- **Runtime Python portable embarqué**, wheels **binaires** uniquement.
- **Code et données séparés** : les données vivent dans `%ProgramData%\FlexoSuite`,
  hors du dossier de code. Une mise à jour ne peut rien détruire.
- **Mono-tenant** : une installation = un imprimeur. Aucune colonne de portée.

Le pont développement / package est `NEXT_PUBLIC_API_URL` : deux ports en
développement, variable **retirée** au build → base d'API relative → mono-port.

## Invariants métier — STOP sans validation d'Eric

- Le **calage est lié à l'OUTIL** (plaque + clichés), pas à la bobine.
  `nb_calages = 1 + nb_changements`.
- **Ø bobine = épaisseur RÉELLE** de la matière.
- **X = laize, Y = développé**, toujours.
- Ordre du devis : **Format → Outil → Matière → Bobinage**.
- Séparation des sources de vérité : la **géométrie** d'un côté, les **tarifs**
  de l'autre.

## Conventions

- **Tout en français** dans le code, y compris les noms de variables.
- Conventional Commits, **sans `Co-Authored-By`**.
- **TDD sur le moteur** : les montants dorés passent en test **avant**
  l'implémentation.
- 1 lot = 1 instance = 1 PR. **CC1 ne touche que `backend/`, CC2 que
  `frontend/`.** Ce qui est commun (`docs/`, `deploy/`, contrat d'API)
  appartient à une seule instance à la fois, annoncée dans `docs/REPRISE.md`.
- ⛔ **Jamais de merge sur rouge** — on attend le job `test`, pas seulement le
  build.
- Quand le contrat d'API bouge : `docs/CONTRAT-API.md` mis à jour, **backend
  livré en premier**. L'inverse envoie le front en 422.
