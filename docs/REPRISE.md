# Reprise — où en est FlexoSuite v2

> État **réel**, pas l'intention. À relire en premier au démarrage de toute
> session, avec `docs/PLAN.md`. `git fetch -p` avant tout état git.

## En-tête

- **Date** : 2026-08-20
- **Lot en cours** : **lot 2 — données et API**. Sous-lot **2a livré**
  (modèle, migrations, session) ; 2b et 2c à venir. Lots 0, 1 et 3 livrés.
- **Portes G0, G1 et G2** : ✅ **franchies** (détail et critères dans
  `docs/PLAN.md`).
- **Contrat d'API** : **v1.1**. La v1 avait été annoncée **avant écriture** ;
  la v1.1 est la **livraison** du lot 2a, pas un changement de forme. Chaque
  section porte son **état de livraison** ; le journal des changements ouvre le
  document.
- **Qui tient quoi** : **CC1** tient `backend/`, `docs/` et `deploy/`. **CC2**
  tient `frontend/` — lot 3 livré et mergé.
  ⚠️ `docs/CONTRAT-API.md` **ne bouge plus sans annonce**, et le backend est
  livré **avant** le front à chaque évolution.

## Mergé sur `main`, ou seulement en PR — au 20/08/2026

La distinction compte : une PR ouverte n'est **pas** l'état du dépôt. Ce qu'un
autre poste obtient par `git pull` s'arrête à la première colonne.

| PR | Objet | État |
| --- | --- | --- |
| #1 à #6 | contrat v0, moteur, montants dorés, contrat v1, front lot 3 | **mergées** |
| #7 | les sept constats de l'audit externe — CORS, états de livraison, cookie, codes d'erreur | **mergée** |
| #9 | front : aiguillage sur le code d'erreur, réglage CORS documenté dans `frontend/AGENTS.md` | **mergée** |
| #10 | contrôles du front câblés dans le check requis, exemple CORS à un seul hôte, CI en Node 24 | **mergée** — `main` à `0c1622a` |
| #8 | `frontend/.env.example` versionné, exception de chemin dans `.gitignore`, configuration de dev au README | **mergée** — `main` à `c12749a` |
| #11 | **lot 2a** : modèle mono-tenant, migrations, installation et session | **ouverte — chez l'audit** |

Plus rien en attente d'audit à l'ouverture du lot 2 : le recouvrement de #8 et
#10 sur `backend/app/config.py` a été résolu au rebase — #8 avait abandonné
entièrement sa version du bloc au profit de celle de #10.

## Fait

- **Dépôt créé**, documentation et garde-fou de confidentialité. Aucun code
  applicatif.
- **`docs/SPEC-METIER.md`** — les formules des 7 postes de coût, les invariants,
  et le **jeu doré** fabriqué :
  - deux ateliers fictifs — l'un rond pour la lisibilité, l'autre non rond
    pour exercer les arrondis et l'ordre des opérations ;
  - passés dans l'ancien moteur en local, avec la **structure** des payloads de
    référence ;
  - **cinq montants dorés** : deux mono-lot (1 777,00 € avec l'atelier rond,
    1 587,66 € avec l'atelier non rond) et trois multi-lots (585,36 · 920,72 ·
    1 170,72) qui verrouillent la règle du calage ;
  - la chaîne de pose en 7 étapes, les 8 sens, le « format approchant », la
    structure des 4 barèmes, la règle silhouette et le modèle de données.
- **`tests/test_confidentialite_livraison.py`** — vert. Il vérifie **ce qu'on
  livre** : aucune valeur de tarif écrite en dur hors du module de fixtures, et
  la marge comme unique chiffre livré.

## Décisions qui structurent la suite

- **Aucun chiffre de l'atelier historique n'entre ici** — ni tarif, ni barème
  réglé sur un parc existant, ni nom, ni commentaire qui le nomme. Ce qui se
  publie : formules, invariants, chaîne de pose, **structure** des barèmes.
- **Les valeurs de référence se fabriquent** : jeu doré → ancien moteur → les
  montants obtenus font foi. **Pas de vérification croisée** avec une baseline
  antérieure : elle n'apporterait rien, les attendus sortent d'un moteur validé.
- **L'application se livre à zéro tarif.** Un assistant de calibration les fait
  produire à l'installation, à partir de chiffres que l'imprimeur connaît :
  amortissement de presse, heures productives, énergie, maintenance ; grille de
  la convention collective des industries graphiques ; catalogue de son
  photograveur. Les barèmes partent **neutres** puis s'ajustent sur ses derniers
  travaux.
- **Marge 30 %** par défaut — décision commerciale, **confirmée explicitement**
  par l'imprimeur à l'installation. Où elle se lit, constaté et non supposé :
  le paramètre de coûts, stocké en pourcentage — ni sur l'entreprise, ni via un
  repli.
- **Conséquence** : le paramétrage de recette et le paramétrage d'installation
  sont **deux choses distinctes**. Le premier vit dans les fixtures de test, le
  second est vide de tarifs.

## Lot 0b — livré et éprouvé

- Backend FastAPI + Alembic sur SQLite, **mono-port** : le même processus sert
  l'API et le front exporté. Vérifié sur le package installé — **un seul port en
  écoute**.
- Front Next en **export statique conditionnel** (`NEXT_OUTPUT=export`), base
  d'API relative dans le package.
- `deploy/windows/` complet, y compris **`reinitialiser-mot-de-passe.bat`** — le
  script qui manquait au patron de référence.
- CI en deux jobs **requis** sur `main`. Le job `build` refuse route API Next,
  middleware et server action ; le job `test` vérifie aussi qu'il n'y a **qu'une
  seule tête** de migration.
- **Next passé en 16** : la version initiale portait une CVE. Audit à zéro
  vulnérabilité — on ne livre pas ça chez un imprimeur.
- `docs/CONTRAT-API.md` v0 — le document que CC2 lit comme une loi.

## Lot 1 — livré, et ce qu'il a appris

- **40 tests verts**, écrits avant le code. Chaque poste est vérifié séparément.
- **L'arrondi est reproduit, pas normalisé** : un arrondi pour Matière, Encres,
  Calage, Roulage et Main d'œuvre ; **deux** pour Finitions ; **trois** pour
  Outillage. Encres et Outillage font pourtant la même chose — Encres somme
  **brut**. Les deux incohérences sont dans le code, commentées comme telles.
- ⚠️ **Les trois montants dorés multi-lots ont dû être corrigés** : ils sortaient
  d'une matière hors jeu doré (le moteur multi-lots lit le **complexe**, pas la
  matière). Trouvé en dumpant la décomposition **avant** d'écrire le moteur.
  Les trois invariants n'avaient rien signalé — ils sont vrais quelle que soit la
  matière. **Un total ne se surveille pas tout seul.**
- **Le métrage monte deux fois** : nombre de tours plafonné, **puis** métrage
  arrondi au mètre supérieur. L'oublier fausse quatre postes à la fois.

## Lot 3 — le front, livré par CC2

Replié ici pour que l'état du projet tienne en un seul document.

- **Socle** : Tailwind v4, ESLint 9, `globals.css` clair et sombre — le squelette
  n'en avait aucun, alors que `npm run lint` est exigé vert. `src/lib-api.ts` a
  laissé la place à `src/lib/api/` (types du contrat, client, façade).
- **L'optimisation est le point d'entrée unique** : brief puis configurations en
  cartes, **dans l'ordre reçu** — le tri du backend n'est pas rejoué. Moins de
  trois propositions est présenté comme normal ; l'absence d'outil compatible
  mène à une proposition chiffrée, pas à un échec ; `ml_total` s'affiche tel quel.
- **Les trois obligations du chiffrage sont tenues** : coefficient à côté du
  pourcentage avec la phrase qui dit que ce n'est pas un taux de marque, détail
  par lot, calage mutualisé nommé.
- **Les 8 sens sont dessinés par leurs deux vues**, avec un glyphe asymétrique
  **dans les deux axes** — une forme symétrique rendrait 0 et 180° indiscernables.
  Le piège des paires est traité de front : face imprimée écrite en toutes
  lettres, sens jumeau nommé.
- **Rien n'est figé** sur la session, la redirection au 401 ni l'écran
  d'installation — conformément à l'annonce du contrat v1.
- Recette passée : lint et build en export verts, export servi par le backend en
  mono-port **sans URL absolue dans le bundle**, écrans essayés en 1280 et en
  390 de large, dégradation sans backend vérifiée.
- **PR #9** (mergée) : le client d'API s'aiguille sur le **code d'erreur** du
  contrat, pas sur le texte ; **10 tests Vitest** ; `frontend/AGENTS.md`
  documente le réglage backend `CORS_ORIGINES`.

## Correction transversale du 20/08 — CI et exemple CORS (PR #10)

Deux constats remontés par CC2, sans effet sur le métier ni sur un montant doré.

- **Les tests du front ne tournaient que chez CC2.** La CI se contentait de
  `npm ci` puis `npm run build` : les 10 tests Vitest et le lint n'étaient
  vérifiés nulle part en intégration. Ils sont désormais exécutés **dans le job
  `build`**, dans l'ordre lint → test → build, tous depuis `frontend/`.
  Le choix du job n'est pas cosmétique : `build` est un check **requis** sur
  `main`. Un troisième job ne le serait pas tant que la protection de branche ne
  le réclame pas — il pourrait échouer sans rien empêcher.
  ⚠️ **Le câblage a immédiatement trouvé quelque chose** : la CI tournait sur
  **Node 20**, que `jsdom` ne supporte pas (`^22.22.2 || ^24.15.0 || >=26`). Le
  premier run est sorti en `webidl.util.markAsUncloneable is not a function`,
  côté undici — un message qui ne nomme pas le vrai problème. **Node 24** en
  intégration, la version du poste de développement.
- **L'exemple CORS de `backend/app/config.py` mélangeait `127.0.0.1` et
  `localhost`.** Remplacé par une origine unique, avec l'avertissement et le
  renvoi au README. Le port n'entre pas dans la définition de *same-site*,
  **l'hôte si** : les mélanger donne un cookie `SameSite=Strict` qui ne tient
  pas, **sans message d'erreur**. Un exemple qui modèle la mauvaise pratique
  finit recopié.

## Lot 2a — le socle : modèle, migrations, session

- **Mono-tenant, et ça se voit dans le schéma** : trois tables (`utilisateur`,
  `session_utilisateur`, `parametres_couts`), **aucune colonne de portée**,
  aucun scope à vérifier. Toute une famille de bugs de fuite entre clients
  disparaît avec la colonne qui les portait.
- **La session est une TABLE, pas un jeton signé.** Le contrat impose la
  révocation côté serveur, et **un jeton signé ne se révoque pas**. Le jeton
  n'est jamais stocké en clair : la base ne garde qu'une empreinte SHA-256.
- **Zéro dépendance ajoutée** : hachage PBKDF2-HMAC-SHA256 de la bibliothèque
  standard. Ces modules partent chez le client dans un **Python embarqué**, où
  seuls des wheels binaires entrent — une bibliothèque qui compile à
  l'installation bloquerait une imprimerie un dimanche soir.
- **`reinitialiser_admin.py` fait enfin ce qu'il promet**, et son test provisoire
  a été remplacé par un test de comportement réel — pas supprimé. Il **révoque
  toutes les sessions ouvertes** : changer un mot de passe sans fermer les portes
  déjà ouvertes ne protège de rien.
- **L'installation part à zéro tarif.** Les neuf paramètres de coûts sont NULL ;
  seule la marge est posée, parce que c'est une décision **commerciale** et non
  un tarif. `calibration_faite` vaut donc faux juste après l'installation.

### Deux défauts du squelette trouvés en chemin

- **Le gabarit de migration importait `sqlmodel`**, une dépendance absente du
  projet : *toute* migration autogénérée était inimportable. Corrigé à la
  racine, dans `alembic/script.py.mako`.
- **Les types SQL maison se rendaient en `app.models.types_sql.DecimalTexte`**
  dans les migrations : une migration déjà appliquée chez un client se serait
  mise à dépendre d'un module qu'on est libre de renommer. Un `render_item`
  dans `alembic/env.py` les rend désormais en `sa.String` — même DDL, aucune
  dépendance au code de l'application.

### Pourquoi un type SQL maison

SQLite ne connaît que INTEGER, REAL et TEXT : le `Numeric` de SQLAlchemy y passe
par un **flottant**. Sur une application de devis dont les montants dorés
tombent au centime, ce n'est pas négociable. `DecimalTexte` stocke la valeur
telle qu'elle a été calculée. Limite assumée et écrite : **aucun tri SQL** sur
ces colonnes, il serait lexicographique.

## Prochaine étape

**Lot 2b — référentiels et paramètres.** Machines, cylindres, matières, outils,
clients, options, barèmes, et les paramètres de coûts. **Le contrat est déjà
annoncé en v1.2** — sections 5 et 6 écrites champ par champ, deux codes
d'erreur ajoutés (`reference_utilisee`, `deja_existant`), enveloppe de liste
uniforme. Rien n'en est implémenté : l'annonce précède l'écriture, comme pour
la v1.

Puis **lot 2c — optimisation, chiffrage, devis**, où le moteur du lot 1 est
enfin branché sur une API.

Reste aussi au moteur : l'**optimiseur** qui choisit entre configurations. Il a
besoin des barèmes, donc du lot 2.

**Ce que CC2 peut débloquer maintenant** : l'écran d'installation, la connexion,
la redirection au 401 et l'aiguillage sur `installation_faite` /
`calibration_faite`. Ils étaient volontairement non figés au lot 3 — le backend
est passé devant, ils peuvent l'être.
