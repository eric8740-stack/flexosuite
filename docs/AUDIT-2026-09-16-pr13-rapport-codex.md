## Verdict

Audit limité au diff exact `lot/2b-referentiels...lot/2b-parametres` (`1f969b4...45319ef`), en lecture seule.

Je ne relève aucun défaut CRITIQUE, mais je déconseille le merge en l’état à cause de deux constats ÉLEVÉS :

- les paramètres tarifaires acceptent des valeurs négatives ou incohérentes ;
- l’initialisation à la volée des barèmes n’est pas sûre sous concurrence.

### 1. ÉLEVÉ — Les paramètres acceptent des coûts négatifs et une marge hors limites

- Fichier : `backend/app/schemas/parametres.py`, lignes 63–73.
- Constat : seul `marge_confort_roulage_mm` impose `ge=0`. Tous les montants, la marge et le facteur de surcoût acceptent des valeurs négatives ; la marge accepte aussi une valeur supérieure à 100.
- Preuve : `Decimal2`/`Decimal4` quantifient la précision mais ne posent aucune borne. Le modèle persistant affirme pourtant que la marge est dans `0–100` (`backend/app/models/noyau.py`, commentaire ligne 104).
- Impact : une saisie comme `cout_operateur_eur_h: "-50.00"` ou `surcout_forme_speciale_facteur: "-2.00"` rend `calibration_faite=true` et alimentera ensuite le moteur avec des coûts négatifs. C’est un risque direct de devis métier faux.
- Correction recommandée : poser au minimum `ge=0` sur les coûts, `gt=0` sur le facteur et formaliser la borne métier de la marge, vraisemblablement `0 <= marge_standard_pct <= 100`. Ajouter des tests 422.
- Risque de la correction : faible avant livraison du front ; elle devient cassante si le front compte déjà sur des valeurs négatives. La borne supérieure de marge reste à valider métier.

### 2. ÉLEVÉ — `assurer_baremes()` n’est pas idempotent sous accès concurrent

- Fichier : `backend/app/services/baremes.py`, lignes 25–44.
- Constat : l’algorithme fait `SELECT`, puis quatre `INSERT`, puis `COMMIT`. Deux premières requêtes simultanées peuvent toutes deux constater les lignes absentes.
- Preuve : la clé primaire empêche les doublons, mais la seconde transaction recevra une `IntegrityError` au `commit`, non interceptée. L’idempotence testée ne couvre que des appels séquentiels.
- Impact : une première ouverture simultanée par plusieurs appels du front peut produire un 500. Avec SQLite, le résultat exact peut être soit une collision de clé primaire, soit temporairement un verrouillage, selon l’entrelacement.
- Correction recommandée : utiliser une insertion atomique SQLite `INSERT ... ON CONFLICT DO NOTHING`, sans lecture préalable, puis laisser le routeur relire les quatre lignes. Ne pas masquer indistinctement toutes les `IntegrityError`.
- Risque de la correction : faible à moyen ; il faut vérifier la compatibilité de la syntaxe avec la version SQLite embarquée.

### 3. MOYEN — `neutre` ne peut pas être déduit correctement d’un dictionnaire libre

- Fichier : `backend/app/models/baremes.py`, lignes 50–64.
- Constat : `not any(bool(valeur) for valeur in donnees.values())` ne mesure ni la neutralité des coefficients ni même de façon fiable l’absence de calibration.
- Exemples :

  - `{"coefficient": 0}` → `neutre=true`, alors que zéro est un effet maximal, pas neutre.
  - `{"points": [], "version": 1}` → `neutre=false`, sans aucun point calibré.
  - `{"points": [], "commentaire": "..."}` → `neutre=false`.
  - `{"points": [{"coefficient": 1.0}]}` → `neutre=false`, alors que le coefficient est mathématiquement neutre.
  - Toute liste non vide est vraie, quel que soit le contenu de ses éléments.

- Impact : le front peut présenter un barème réellement actif comme neutre, ou inversement annoncer une calibration inexistante. À terme, ce booléen ne sera pas fiable pour prévenir que les scores sont indicatifs.
- Correction recommandée : soit définir et valider un schéma propre à chaque type de barème puis calculer la neutralité sémantique, soit définir explicitement `neutre` comme « structure vide » et tester uniquement la structure canonique attendue. Tant que `donnees` reste libre, un calcul fiable est impossible.
- Risque de la correction : moyen : figer les quatre formats peut être cassant pour le futur front. C’est néanmoins le bon moment, avant son implémentation.

### 4. MOYEN — Le test de migration a perdu la vérification du DDL complet

- Fichier : `backend/tests/test_migration_referentiels.py`.
- Constat : la fonction `_schema()` et le test comparant le DDL avant/après ont été supprimés. Le nouveau test vérifie seulement la présence ou l’absence des noms de tables.
- Preuve : une migration créant `bareme` avec une colonne manquante, une mauvaise nullabilité ou sans clé primaire laisserait ce test vert.
- Impact : le test ne prouve plus que la migration revient au même schéma après `upgrade → downgrade → upgrade`. Il prouve seulement que la table disparaît puis réapparaît.
- Correction recommandée : conserver le contrôle de DDL complet et l’adapter à la dernière migration, en plus du contrôle ciblé des tables.
- Risque de la correction : uniquement un risque de fragilité de normalisation du DDL SQLite, déjà traité dans la version supprimée.

### 5. MOYEN — Le `downgrade` est structurellement réversible, mais détruit les calibrations

- Fichier : `backend/alembic/versions/38af14d3d6c7_baremes.py`, lignes 45–49.
- Constat : `downgrade()` supprime intégralement `bareme`.
- Impact : après utilisation de cette version, un rollback efface définitivement les courbes calibrées. La remontée recréera des barèmes neutres au prochain accès. Le schéma revient, les données non.
- Correction recommandée : soit assumer et documenter explicitement que le downgrade est destructif et exiger une sauvegarde, soit prévoir une procédure de rollback applicative avec export/restauration des quatre JSON. Une migration Alembic seule ne peut pas conserver naturellement des données d’une table supprimée.
- Risque de la correction : une migration de sauvegarde temporaire complexifierait inutilement le schéma. La solution minimale est probablement opérationnelle et documentaire.

### 6. MOYEN — Les champs ignorés peuvent masquer une mise à jour du mauvais barème

- Fichier : `backend/app/schemas/parametres.py`, lignes 143–157, et `backend/app/routers/baremes.py`, lignes 72–87.
- Constat : `type` et `libelle` sont acceptés puis ignorés même s’ils contredisent l’URL.
- Preuve : le test exige que `PUT /baremes/echenillage` avec `"type": "effet_banane"` modifie silencieusement `echenillage`.
- Impact : une erreur d’état ou de routage du front peut écrire les données d’un barème dans un autre sans aucun signal. C’est une corruption fonctionnelle silencieuse.
- Correction recommandée : continuer à accepter ces champs pour permettre le renvoi de l’objet lu, mais répondre 422 s’ils sont présents et différents du barème ciblé. `neutre` peut rester ignoré car il est réellement calculé.
- Risque de la correction : faible ; seul un payload déjà incohérent devient refusé.

### 7. FAIBLE — Le `commit()` du service a une portée plus large que son nom

- Fichier : `backend/app/services/baremes.py`, ligne 44.
- Constat : `db.commit()` valide toutes les modifications en attente dans la session, pas seulement les quatre barèmes.
- Impact actuel : dans les deux appelants présents, `assurer_baremes()` est appelé avant toute modification métier ; je n’ai donc pas identifié de validation parasite actuelle.
- Impact futur : un appel après modification d’un autre objet introduirait une frontière transactionnelle invisible et empêcherait le routeur de tout annuler ensemble.
- Correction recommandée : ne pas committer dans ce service ; faire un `flush()` atomique et laisser la couche requête décider du commit. Cela peut être combiné à la correction de concurrence.
- Risque de la correction : moyen si les GET doivent créer durablement les lignes ; il faut alors définir explicitement la transaction du GET.

## Réponses aux points prioritaires

1. **Contrat et JSON** — Les onze clés sont bien rendues : dix champs persistants plus `calibration_faite`. Les décimaux sortent en chaînes ; `marge_confort_roulage_mm` sort en entier. Ce choix est défendable et cohérent avec le moteur, qui le type déjà comme `int`. Les barèmes utilisent bien `{elements, total}`. Les statuts nominaux sont 200 et les erreurs examinées gardent `{code, detail}`.

2. **Précisions du contrat** — Quatre décimales pour un tarif au m² et le refus de `marge_standard_pct:null` sont cohérents. La validation d’existence de `machines_ids` est une véritable précision. Accepter puis ignorer `type`/`libelle` est en revanche une extension de la forme d’écriture et comporte le risque décrit au constat 6.

3. **Deux sémantiques de `PUT`** — Le `PUT` partiel des coûts correspond bien au parcours d’assistant et `exclude_unset` est correctement employé. Le risque principal est cognitif pour le front : il faut une méthode cliente explicitement nommée comme partielle. Pour les référentiels, attention au fait que les champs ayant des valeurs par défaut peuvent être réinitialisés si le front les omet ; je ne réaudite pas ici la PR #12.

4. **POST de calibration en démo** — Risque immédiat faible pour les données : la fonction est réellement pure aujourd’hui. Risque immédiat moyen sur le contrat, car l’exception contredit la règle simple « toute écriture/méthode d’écriture = 403 ». Risque futur plus important : le test sentinelle fige le 200 et peut inciter à conserver l’exception si l’endpoint gagne plus tard de la journalisation ou une persistance. Il faut reformuler la règle autour des mutations d’état et imposer un test de pureté/non-modification.

5. **Formule et exemple** — Oui : `240000 / 10 / 1600 = 15,00`, `12000 / 1600 = 7,50`, `8000 / 1600 = 5,00`, total `27,50`. L’ancien exemple à 250 000 € aurait donné `15,63 + 7,50 + 5,00 = 28,13`. La correction à 240 000 € est exacte ; je n’ai trouvé aucune autre occurrence documentaire de l’ancien chiffre dans le périmètre.

6. **Neutralité** — Le calcul n’est sûr que pour une convention très étroite : toutes les valeurs de premier niveau doivent être vides ou fausses. Il est incorrect dès que le dictionnaire accueille métadonnées, zéros significatifs ou structures non vides sémantiquement neutres.

7. **Création à la volée** — Idempotente en séquence, pas sous concurrence. Et oui, le `commit()` peut valider autre chose déjà présent dans la session, même si les appelants actuels ne créent pas encore ce cas.

8. **Migration** — Le DDL descend et remonte, mais les données de calibration sont perdues. Le test actuel vérifie la dernière migration uniquement, ce qui est logique pour `downgrade -1`, mais il ne vérifie plus le schéma complet qu’il prétendait auparavant protéger.

Enfin, `machines_ids` avec une machine désactivée respecte littéralement « l’identifiant existe ». Le comportement fonctionnel futur reste **À confirmer** : si l’optimiseur ignore les machines désactivées, un barème qui ne cible qu’elles deviendra inapplicable sans erreur. Il faut décider si l’affectation historique à une machine inactive doit rester autorisée avant d’ajouter une contrainte.
