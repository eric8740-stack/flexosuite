# Reprise — où en est FlexoSuite v2

> État **réel**, pas l'intention. À relire en premier au démarrage de toute
> session, avec `docs/PLAN.md`. `git fetch -p` avant tout état git.

## En-tête

- **Date** : 2026-09-16
- **Lot en cours** : **lot 2 — données et API**. Sous-lots **2a, 2b-1 et 2b-2
  mergés** (`main` à `5375f6f`) — le lot 2b est **clos**. **2c** est la suite :
  optimisation, chiffrage, devis. Lots 0, 1 et 3 livrés.
- **Portes G0, G1 et G2** : ✅ **franchies** (détail et critères dans
  `docs/PLAN.md`).
- **Contrat d'API** : **v1.2 livrée**, annoncée le 20/08 **avant écriture**.
  Sections 5 et 6 en ✅. Chaque section porte son **état de livraison** ; le
  journal des changements ouvre le document, en antéchronologique.
- **Qui tient quoi** : **CC1** tient `backend/`, `docs/` et `deploy/`. **CC2**
  tient `frontend/` — lot 3 livré et mergé.
  ⚠️ `docs/CONTRAT-API.md` **ne bouge plus sans annonce**, et le backend est
  livré **avant** le front à chaque évolution.

## Mergé sur `main`, ou seulement en PR — au 16/09/2026

La distinction compte : une PR ouverte n'est **pas** l'état du dépôt. Ce qu'un
autre poste obtient par `git pull` s'arrête à la première colonne.

| PR | Objet | État |
| --- | --- | --- |
| #1 à #6 | contrat v0, moteur, montants dorés, contrat v1, front lot 3 | **mergées** |
| #7 | les sept constats de l'audit externe — CORS, états de livraison, cookie, codes d'erreur | **mergée** |
| #9 | front : aiguillage sur le code d'erreur, réglage CORS documenté dans `frontend/AGENTS.md` | **mergée** |
| #10 | contrôles du front câblés dans le check requis, exemple CORS à un seul hôte, CI en Node 24 | **mergée** — `main` à `0c1622a` |
| #8 | `frontend/.env.example` versionné, exception de chemin dans `.gitignore`, configuration de dev au README | **mergée** — `main` à `c12749a` |
| #11 | **lot 2a** : modèle mono-tenant, migrations, installation et session | **mergée** — `main` à `5b5532f` |
| #12 | **lot 2b-1** : les six référentiels | **mergée** le 16/09 — audit Codex traité et corrigé |
| #13 | **lot 2b-2** : paramètres, calibration, barèmes | **mergée** le 16/09 — audit Codex traité et corrigé, rebasée sur `main`. `main` à **`5375f6f`**, CI verte. |

### Audits du 16/09/2026 — ce qu'ils ont changé

Les deux PR du lot 2b ont été auditées par Codex le même jour. Les rapports, les
analyses Claude figées **avant lecture** et les verdicts sont dans `docs/` :
`AUDIT-2026-09-16-pr12.md` et `AUDIT-2026-09-16-pr13.md`.

- **PR #12 — corrigée.** Quatre constats traités, `1f969b4`. Le `PUT` des
  référentiels exige désormais **tous** les champs (il réinitialisait en silence
  ceux qui avaient un défaut — un `PUT` sans `actif` réactivait un élément
  désactivé) ; la nullabilité de quatre champs est reclassée **CASSANTE** au
  contrat, avec consigne à CC2 ; le test de migration compare le **DDL complet** ;
  une course sur `DELETE` rend 409 au lieu de 500. **232 tests**, les 8 neufs
  vérifiés **dans les deux sens**.
- **PR #13 — corrigée.** Sept constats, deux ÉLEVÉS. Les paramètres tarifaires
  sont **bornés** (coûts ≥ 0, facteur ≥ 1, marge 0–500 — arbitrage d'Eric ; avant,
  `-50,00` passait en 200 avec `calibration_faite=true`) ; `assurer_baremes()`
  passe en `ON CONFLICT DO NOTHING` **sans lecture préalable** ; `neutre` se lit
  sur `donnees.points` ; un `type` qui contredit l'URL répond 422 ; l'aller-retour
  de migration descend jusqu'à `base`. **334 tests verts**, chaque correction
  vérifiée **dans les deux sens**.

✅ **Tout est mergé, `main` est vert.** Le conflit sur `docs/CONTRAT-API.md` a
été résolu à la main lors du rebase :
le bloc « ⚠️ CASSANT » de la #12 est conservé **et** les ajouts de la #13 aussi.
L'affirmation « rien de ce qui avait été annoncé n'a changé de forme », que la
#13 réintroduisait, n'a **pas** été reprise — c'est exactement ce que l'audit de
la #12 a démenti.

⚠️ **Le piège du `downgrade -1` s'est déclenché pour de vrai au rebase**, et il
n'était dans aucun rapport : le test de destruction des données, écrit pour les
référentiels, est devenu faux dès que la migration des barèmes s'est empilée
(`-1` ne défaisait plus `machine`). La suite post-rebase était à **1 échec /
270 passés**. Réancré sur `base`. **Ne jamais ancrer un contrôle de migration
sur « la dernière ».**

✅ **Bornes de la section 5 — il n'y avait rien à corriger.** Annoncé comme
« reste ouvert » par erreur : la mesure a montré que les 23 champs numériques
étaient **déjà bornés** depuis leur écriture. Seules les deux clés étrangères
n'étaient pas bornées au niveau du schéma, mais l'API rendait déjà 422 en
nommant le champ — comportement observable correct. Les bornes sont désormais
**verrouillées par 27 tests** (vérifiés : retirer trois bornes en fait rougir
quatre) et **écrites au contrat**.

**Total au 16/09 : 361 tests verts, 5 ignorés.**

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

## Lot 2b-1 — les six référentiels

- **Un seul routeur CRUD, instancié six fois** (`app/routers/referentiels.py`).
  Ce qui est propre à chaque ressource — clés uniques, clés étrangères,
  désignation française — est **déclaré** dans une `Ressource` et nulle part
  ailleurs. Six fichiers presque identiques auraient fini par ne plus l'être, et
  une pagination corrigée dans cinq routeurs sur six ne se voit pas à la
  relecture.
- **Les gardes sont posées sur le routeur, pas sur chaque endpoint**, dans
  l'ordre voulu : `exiger_session` (401) puis `interdire_ecriture_demo` (403).
  Aucun endpoint ne peut les oublier.
- **`est_reference()` est un point unique** (`app/services/referentiels.py`) :
  le lot 2c ajoutera les devis en étendant le dictionnaire `LIENS`, **pas en
  écrivant une deuxième fonction**.
- **L'unicité est tranchée par la BASE**, pas par une lecture préalable : la
  contrainte SQL ne laisse pas de fenêtre entre le contrôle et l'insertion. La
  relecture qui suit ne sert qu'à **nommer** le champ fautif dans le `detail`.
- **Nouveau type SQL `JsonTexte`** pour `modules`, `modules_requis` et
  `tarification`. Même limite assumée que `DecimalTexte` : **aucune requête SQL
  ne filtre dessus**, le filtrage se fait en Python.
- **221 tests verts** (77 avant), dont l'aller-retour de migration joué en
  sous-processus sur une base vierge — la commande même que joue `install.bat`
  chez le client, et l'état constaté avec `sqlite3`, pas avec la sortie
  d'Alembic.

### Ce que le banc de mutations a trouvé

Sept mutations jouées, **six rouges** — et **une verte**, qui est le vrai
résultat :

> **Retirer `.order_by(id)` du routeur ne fait rougir aucun test.** Sur SQLite,
> l'ordre naturel d'un `SELECT` sans tri coïncide avec l'ordre des identifiants.
> Le test attrape un ordre explicite **faux** (tri inversé : rouge, vérifié), il
> n'attrape pas un ordre **absent**. La limite est écrite dans le docstring du
> test, pour qu'on ne le croie pas plus fort qu'il n'est.

C'est le rappel du lot 1, dans une autre matière : **une suite verte ne dit rien
de ce qu'elle ne couvre pas.**

## Lot 2b-2 — paramètres, calibration, barèmes

- **Le seul `PUT` partiel du contrat**, et la raison est dans l'usage : ces
  valeurs s'enregistrent **champ par champ**, au fil de l'assistant. Un champ
  absent du corps n'est pas mis à `null`, il n'est pas touché — `exclude_unset`,
  et non un `model_dump()` ordinaire qui rendrait les défauts comme s'ils
  avaient été envoyés.
- **`calibration_faite`, `neutre` : calculés, jamais stockés.** Un booléen rangé
  à côté de la donnée qu'il décrit finit par la contredire — il suffit d'un
  chemin d'écriture qui oublie de le mettre à jour.
- **L'assistant de calibration propose, il n'enregistre pas.** Fonction pure,
  aucun accès base. C'est un `PUT` sur les paramètres qui décide : un assistant
  qui écrirait tout seul retirerait à l'imprimeur le seul moment qui compte.
- **Le taux est la somme des lignes arrondies**, pas le total arrondi une fois.
  Un centime d'écart possible, assumé : le détail existe pour être additionné.
- **Les quatre barèmes se créent à la volée** au premier accès — ni migration,
  ni installation. Le lot 2a est déjà sur `main` et peut avoir été installé :
  une base créée avant ce lot doit retrouver ses barèmes sans intervention.
- **`Page` a quitté le routeur des référentiels** pour `app/schemas/enveloppe.py`
  quand les barèmes en ont eu besoin. Une enveloppe recopiée d'un routeur à
  l'autre finit par différer, et le front écrirait deux lectures de liste.

### Deux choses trouvées en écrivant

> **L'exemple de calibration du contrat se contredisait** : les entrées données
> (250 000 € sur 10 ans, 1 600 h) donnent 28,13 €/h, pas les 27,50 € de la
> réponse d'exemple. C'est 240 000 € qui donne 27,50. Corrigé — un exemple faux
> finit recopié en fixture par le front. Même famille que le « 94 dents ×
> 3,175 mm = 298,45, pas 300 » relevé à la v1.2.

> **`POST /api/calibration/taux-machine` n'est pas soumis à la garde du mode
> démo** — c'est un `POST` qui n'écrit rien, et le refuser priverait la démo
> publique de son meilleur écran. **Décision à valider par Eric** : c'est le
> seul endroit du projet où une méthode d'écriture échappe à la garde. Un test
> sentinelle la réclame, et il tombera si on remet la garde.

- **221 → 260 tests verts.** Banc de mutations du 2b-2 : **huit jouées, huit
  rouges**, dont la sentinelle du mode démo.

## Prochaine étape

**Lot 2c — optimisation, chiffrage, devis**, où le moteur du lot 1 est enfin
branché sur une API. Les montants dorés restent la référence : aucun ne bouge.
`est_reference()` s'y étend par le dictionnaire `LIENS`, pas par une deuxième
fonction.

⚠️ **Aucune des deux PR n'est mergée**, et le merge appartient à Eric. La
branche `lot/2b-parametres` est **empilée sur `lot/2b-referentiels`** : si 2b-1
était refusée, 2b-2 demanderait un rebase.

Puis **lot 2c — optimisation, chiffrage, devis**, où le moteur du lot 1 est
enfin branché sur une API.

Reste aussi au moteur : l'**optimiseur** qui choisit entre configurations. Il a
besoin des barèmes, donc du lot 2.

**Ce que CC2 peut débloquer maintenant** : l'écran d'installation, la connexion,
la redirection au 401 et l'aiguillage sur `installation_faite` /
`calibration_faite`. Ils étaient volontairement non figés au lot 3 — le backend
est passé devant, ils peuvent l'être.
