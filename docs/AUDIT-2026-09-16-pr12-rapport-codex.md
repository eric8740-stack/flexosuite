## Verdict

**Modifications demandées avant fusion.**

Le CRUD, les relations actuelles, les formats décimaux et la migration sont globalement cohérents. Deux écarts importants restent néanmoins présents :

1. le `PUT` annoncé comme remplacement complet accepte des corps incomplets et peut effacer silencieusement des valeurs ;
2. la nullabilité ajoutée à certains champs est bien un changement de contrat potentiellement cassant, contrairement au journal v1.2.

Aucune modification n’a été effectuée.

## Constats

### 1. ÉLEVÉ — Le `PUT` « complet » accepte des corps incomplets et réinitialise silencieusement des champs

- **Fichiers :** [referentiels.py](C:/Users/ericp/projets/flexosuite/backend/app/routers/referentiels.py:203), [schemas/referentiels.py](C:/Users/ericp/projets/flexosuite/backend/app/schemas/referentiels.py:23), [CONTRAT-API.md](C:/Users/ericp/projets/flexosuite/docs/CONTRAT-API.md:538)
- **Constat :** `POST` et `PUT` utilisent le même schéma `XxxEcriture`. Plusieurs champs y ont une valeur par défaut. `model_dump()` inclut ces valeurs, puis le routeur les affecte toutes à l’objet existant.
- **Preuve :**
  - une machine envoyée sans `modules` devient `modules=[]` ;
  - un client envoyé sans `contact`, `email` ou `telephone` voit ces champs passer à `null` ;
  - omettre `actif` le remet à `true` ;
  - pour une option, omettre `modules_requis`, `groupes_couleurs_requis` ou `silhouette_automatique` les remet à leurs valeurs par défaut.
- **Impact :** un front incomplet ou écrit contre l’annonce initiale peut perdre des données sans recevoir de 422. Cela contredit « le corps entier est attendu » et l’argument selon lequel le remplacement complet empêche précisément les disparitions silencieuses.
- **Correction recommandée :** conserver le remplacement complet, mais employer des schémas de `PUT` dont tous les champs sont obligatoires — y compris ceux possédant une valeur par défaut au `POST`. Les champs nullables doivent être obligatoirement présents, avec une valeur pouvant être `null`.
- **Risque de la correction :** **moyen**. Les clients qui omettent actuellement les champs à valeur par défaut recevront désormais 422. C’est cassant, mais conforme à la sémantique publiée et préférable avant que le front ne soit écrit.
- **Test manquant :** créer une ressource avec une liste/coordonnée non vide, faire un `PUT` sans ce champ et attendre `422 payload_invalide`.

### 2. ÉLEVÉ — La nullabilité livrée n’est pas une simple précision pour un front déjà écrit

- **Fichiers :** [CONTRAT-API.md](C:/Users/ericp/projets/flexosuite/docs/CONTRAT-API.md:41), [schemas/referentiels.py](C:/Users/ericp/projets/flexosuite/backend/app/schemas/referentiels.py:54), [schemas/referentiels.py](C:/Users/ericp/projets/flexosuite/backend/app/schemas/referentiels.py:94)
- **Constat :** `date_inventaire`, `contact`, `email` et `telephone` étaient montrés comme des chaînes dans le JSON exact annoncé le 20/08. La livraison autorise désormais `null` et affirme qu’aucune forme annoncée n’a changé.
- **Raisonnement :** accepter `null` en entrée est additif pour le backend, mais rendre `null` élargit le type de réponse de `string` vers `string | null`. Un front TypeScript déjà typé d’après le JSON exact peut appeler directement une opération de chaîne et échouer.
- **Impact :** incompatibilité possible avec un front effectivement écrit contre la v1.2 annoncée. `nb_dents` n’est pas concerné : sa nullabilité avait bien été annoncée.
- **Correction recommandée :** ne pas retirer la nullabilité, qui paraît métierement justifiée. Corriger le journal pour la classer comme changement de forme potentiellement cassant et prévenir explicitement CC2. Même remarque pour les quatre champs.
- **Risque de la correction :** **faible**, car elle est documentaire. Rendre de nouveau ces champs non nullables serait beaucoup plus risqué et n’est pas recommandé.

### 3. FAIBLE — Le test de migration ne prouve pas l’identité complète du schéma après le cycle

- **Fichiers :** [test_migration_referentiels.py](C:/Users/ericp/projets/flexosuite/backend/tests/test_migration_referentiels.py:60), [49e79c0d2b7a_referentiels.py](C:/Users/ericp/projets/flexosuite/backend/alembic/versions/49e79c0d2b7a_referentiels.py:28)
- **Constat :** le test `upgrade → downgrade → upgrade` vérifie la présence des tables. Un autre test vérifie les deux clés étrangères uniquement après une montée. Il ne compare ni les index, ni les contraintes uniques, ni la nullabilité avant/après la remontée.
- **Impact :** une régression future pourrait laisser les tables présentes tout en perdant une contrainte ou un index.
- **Correction recommandée :** capturer après chaque montée :
  - `PRAGMA table_info` ;
  - `PRAGMA foreign_key_list` ;
  - `PRAGMA index_list` et `PRAGMA index_info` ;
  puis comparer les deux instantanés.
- **Risque de la correction :** **faible**, uniquement sur les tests.

La migration elle-même est correctement ordonnée : suppression de `outil` avant `cylindre`, puis de `cylindre` avant `machine`; la remontée recrée les deux index FK, les deux FK et toutes les contraintes uniques. **Je n’ai trouvé aucun défaut réel de réversibilité du schéma.** Comme tout downgrade qui supprime des tables, il détruit toutefois les données des six référentiels : la réversibilité constatée est structurelle, pas une restauration des données.

## Réponses aux sept points prioritaires

1. **Contrat JSON et erreurs :** hors constats ci-dessus, les clés correspondent, les listes rendent `{elements, total}`, les décimaux sortent en chaînes et `prix_m2_eur` conserve quatre décimales. Les codes 201/200/204, 401, 403, 404, 409 et 422 suivent le contrat. Les champs inconnus sont refusés.

2. **« Précisions » :**
   - `PUT` complet : précision plausible, mais mal appliquée actuellement ;
   - FK inconnue en 422 : précision compatible ;
   - champ inconnu en 422 : précision compatible ;
   - normalisation décimale : précision compatible, mais elle change volontairement la valeur renvoyée si le front envoie davantage de décimales ;
   - nullabilité de `date_inventaire` et des coordonnées client : **changement de domaine de réponse potentiellement cassant**, pas simple précision.

3. **`est_reference()` / `LIENS` :** machine → cylindre et cylindre → outil sont bien couvertes. Les six routes DELETE passent actuellement par l’unique fonction générique. Pour l’API livrée, le point d’extension est donc unique. Une suppression directe par un futur service contournerait la garde applicative, mais resterait bloquée par les FK SQLite activées.

4. **PUT complet :** le principe cohabite sans ambiguïté avec le PUT partiel des paramètres, puisque les routes diffèrent. L’implémentation actuelle n’est cependant pas sûre contre la perte de données par omission — constat 1.

5. **Ordre des listes :**
   - avec les tables actuelles, `id INTEGER PRIMARY KEY` est l’alias du `rowid`. Une lecture complète prend généralement l’ordre des `rowid`, ce qui explique la mutation verte ;
   - suppression/réinsertion et réutilisation du dernier identifiant ne produisent pas nécessairement un contre-exemple visible ;
   - `VACUUM` ne renumérote pas ces clés primaires déclarées ;
   - `WITHOUT ROWID` n’est pas utilisé.
   
   Malgré cela, SQLite ne garantit aucun ordre sans `ORDER BY`; un autre plan d’exécution ou une évolution du schéma peut diverger. Le `order_by(id)` est donc requis. Par ailleurs, une pagination `OFFSET` peut sauter ou répéter des lignes si des insertions/suppressions surviennent **entre deux appels**, même avec cet ordre. Ce dernier cas n’est pas couvert par le contrat de concurrence actuel.

6. **Migration :** downgrade structurellement correct et remontée conforme au DDL. La preuve automatisée est incomplète sur index/uniques/nullabilité, d’où le constat faible.

7. **`_commettre()` :** `cle is None` peut être atteint autrement que par un doublon concurrent :
   - disparition concurrente d’une FK entre validation et commit ;
   - future contrainte ou trigger non répertorié ;
   - dérive entre modèles et schéma installé.
   
   Relancer l’exception est plus juste que mentir avec `deja_existant`. Un 500 est acceptable pour une contrainte inconnue. Une violation FK identifiée devrait idéalement devenir `422 payload_invalide`; une course pendant DELETE peut également produire un `IntegrityError` non intercepté et donc un 500. Sur SQLite mono-processus, cette fenêtre est étroite mais réelle.

## Vérification

- Diff inspecté : `origin/main...origin/lot/2b-referentiels`, HEAD `58a6712`.
- Aucun fichier suivi modifié.
- Deux briefs d’audit non suivis préexistaient ; ils n’ont pas été touchés.
- `git diff --check` ne signale rien.
- Je n’ai pas pu rejouer pytest dans cet environnement : le Python du venv pointe vers un interpréteur auquel l’exécution est refusée. Le résultat fourni — **221 tests passés**, plus CI `build` et `test` vertes — n’est donc pas contredit, mais n’a pas été reproduit ici.
