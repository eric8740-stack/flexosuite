# Audit demandé — FlexoSuite — 2026-09-16 — PR #13 (lot 2b-2)

## Périmètre

Branche : `lot/2b-parametres`   Base : **`lot/2b-referentiels`** (PR empilée)   PR : **#13**

⚠️ **Le diff à auditer est `lot/2b-referentiels...lot/2b-parametres`, PAS vs `main`.**
Le contenu de la PR #12 est déjà dans la base de celle-ci ; il a son propre audit et
n'est pas à réexaminer ici.

Diff : **20 fichiers, +1318 / −50**

```
backend/alembic/versions/38af14d3d6c7_baremes.py |  49 +++
backend/app/main.py                              |  15 +-
backend/app/models/__init__.py                   |   8 +
backend/app/models/baremes.py                    |  64 +++
backend/app/routers/baremes.py                   |  88 +++
backend/app/routers/calibration.py               |  47 +++
backend/app/routers/parametres.py                |  65 +++
backend/app/routers/referentiels.py              |  15 +-
backend/app/schemas/enveloppe.py                 |  24 +
backend/app/schemas/parametres.py                | 158 +++
backend/app/services/baremes.py                  |  44 ++
backend/app/services/calibration.py              |  88 +++
backend/tests/fixtures/atelier_demo.py           |  58 +
backend/tests/test_baremes.py                    | 189 +++
backend/tests/test_calibration_taux_machine.py   | 147 +++
backend/tests/test_migration_referentiels.py     |  18 +-
backend/tests/test_parametres_couts.py           | 165 +++
docs/CONTRAT-API.md                              |  47 +-
docs/PLAN.md                                     |  10 +-
docs/REPRISE.md                                  |  69 +-
```

## Ce qui a été fait, et pourquoi

Livraison de la **section 6 du contrat d'API** : paramètres de coûts, assistant de
calibration, barèmes. Avec elle, la v1.2 est entièrement livrée.

Décisions structurantes :

- `PUT /api/parametres/couts` est **partiel** (`exclude_unset`) — ces valeurs
  s'enregistrent champ par champ au fil de l'assistant. C'est le seul `PUT` partiel du
  contrat ; les référentiels (PR #12) sont en remplacement complet.
- `calibration_faite` (paramètres) et `neutre` (barèmes) sont **calculés, jamais
  stockés**.
- `POST /api/calibration/taux-machine` est une **fonction pure** : aucun accès base,
  le calcul propose, un `PUT` décide.
- Les **quatre barèmes sont créés à la volée** au premier accès (`assurer_baremes()`),
  ni par la migration ni par l'installation — le lot 2a est déjà sur `main` et peut
  avoir été installé.
- `Page` (l'enveloppe de liste) a été déplacée du routeur des référentiels vers
  `app/schemas/enveloppe.py`.

⚠️ **Contexte à connaître** : ce code a été écrit dans une session configurée avec un
profil de règles différent de celui du projet, conçu/implémenté/validé par **un seul
agent**. Les commentaires du code ne sont pas des preuves.

## Zones sensibles touchées

Base · **migrations** (une nouvelle, `38af14d3d6c7`, aller-retour à vérifier) ·
données persistantes · **API** (contrat v1.2, section 6) · **règles métier**
(`calibration_faite`, barèmes neutres, formule du taux machine).

## Tests

Commande : `python -m pytest -q` dans `backend/`   Résultat : **260 passés, 0 échoué** (mesuré le 16/09/2026 sur `45319ef`)
CI GitHub sur la PR : `build` **pass**, `test` **pass**.

Banc de mutations joué sur ce lot : **8 mutations, 8 rouges**.

**Non couvert** : aucun test de concurrence ; aucun test de volumétrie ; le contenu de
`donnees` d'un barème n'est **pas validé** (dictionnaire libre) ; aucun test ne vérifie
le comportement si la ligne `parametres_couts` manque ; `machines_ids` n'est pas testé
avec une machine désactivée.

## Ce sur quoi je veux ton avis en priorité

1. **Le contrat est-il respecté à la lettre ?** Section 6 de `docs/CONTRAT-API.md`
   contre les JSON réellement rendus : les dix champs + `calibration_faite`, types
   chaîne des décimaux (**sauf `marge_confort_roulage_mm`, rendu en entier** — est-ce
   défendable ?), enveloppe `{elements, total}` des barèmes, codes HTTP et codes
   d'erreur.

2. **Les « précisions » ajoutées au contrat** (journal des changements v1.2, section
   6) : vraies précisions, ou changement de forme pour un front déjà écrit ? En
   particulier : `finitions_prix_m2_eur` à **quatre** décimales, `marge_standard_pct:
   null` explicite en 422, `type`/`libelle`/`neutre` **acceptés et ignorés** au `PUT`,
   `machines_ids` dont chaque identifiant doit exister.

3. **Deux sémantiques de `PUT` dans la même API** : remplacement complet sur les six
   référentiels (PR #12), **partiel** sur `/api/parametres/couts`. Justifié par
   l'usage, ou piège pour le front ? Y a-t-il un risque de perte de données silencieuse
   d'un côté ou de l'autre ?

4. **`POST /api/calibration/taux-machine` en mode démo** : il répond **200** alors que
   le contrat écrit « quand le mode démo est actif, **toute écriture** répond 403 ».
   L'argument retenu : c'est un `POST` qui n'écrit rien, et le refuser priverait la
   démonstration publique de son meilleur écran. **Je veux ton avis sur le RISQUE, pas
   ta préférence** : qu'est-ce qui peut mal tourner, et à quelle échéance ?

5. **La formule du taux machine** (`app/services/calibration.py`) : le taux est la
   **somme des lignes arrondies**, pas le total arrondi une seule fois (écart d'un
   centime possible, assumé). Et **l'exemple du contrat a été corrigé** par cette
   session : l'entrée est passée de 250 000 € à 240 000 €, et la réponse d'exemple
   porte désormais trois lignes (15,00 / 7,50 / 5,00 pour 27,50).
   → **Les trois lignes sortent-elles bien des entrées de l'exemple, au centime ?**
   → La correction de l'exemple est-elle juste, ou a-t-elle introduit une autre
   incohérence ailleurs dans le document ?

6. **`neutre` calculé depuis `donnees`** (`app/models/baremes.py`) : conséquence
   assumée, vider les données remet le barème en neutre. Le calcul
   (`not any(bool(valeur) for valeur in donnees.values())`) est-il correct pour toutes
   les formes de `donnees` qu'un front peut envoyer ? `donnees` n'étant pas validé,
   quels cas produisent un `neutre` faux ?

7. **`assurer_baremes()`** (`app/services/baremes.py`) : la création à la volée est-elle
   réellement idempotente sous accès concurrent ? Et le `db.commit()` qu'elle fait
   au milieu d'une requête peut-il valider autre chose que ce qu'elle a ajouté ?

8. **Migration `38af14d3d6c7`** : `downgrade` réellement réversible ? Et le test
   d'aller-retour, qui ne défait plus que la **dernière** migration, vérifie-t-il encore
   ce qu'il prétend ?

## Ce que je ne veux PAS voir toucher

- `backend/app/moteur/` et les **montants dorés** — zone gelée.
- `frontend/`, `deploy/`.
- Refactoring d'élégance, renommages, réorganisation de fichiers.
- Le contenu de la PR #12 (il a son propre audit).

## Attendu

Audit **EN LECTURE SEULE**. Un constat = gravité (CRITIQUE / ÉLEVÉ / MOYEN / FAIBLE /
OPTIONNEL), fichier, preuve ou raisonnement, impact, correction recommandée, risque de
la correction. Preuve insuffisante → « À confirmer ».

Priorité : exactitude métier > intégrité des données > stabilité > sécurité >
simplicité > maintenabilité > élégance.
