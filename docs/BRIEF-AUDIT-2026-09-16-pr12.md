# Audit demandé — FlexoSuite — 2026-09-16 — PR #12 (lot 2b-1)

## Périmètre

Branche : `lot/2b-referentiels`   Base : `main` (`5b5532f`)   PR : **#12**
Diff : `git diff origin/main...origin/lot/2b-referentiels` — **19 fichiers, +1951 / −22**

```
backend/alembic/env.py                             |   8 +-
backend/alembic/versions/49e79c0d2b7a_referentiels.py | 131 +++
backend/app/erreurs.py                             |  43 +
backend/app/main.py                                |   7 +-
backend/app/models/__init__.py                     |  14 +
backend/app/models/referentiels.py                 | 162 +++
backend/app/models/types_sql.py                    |  36 +-
backend/app/routers/referentiels.py                | 291 +++
backend/app/schemas/decimaux.py                    |  59 +
backend/app/schemas/referentiels.py                | 168 +++
backend/app/services/referentiels.py               |  52 +
backend/tests/aide_referentiels.py                 | 181 +++
backend/tests/fixtures/atelier_demo.py             |  75 +
backend/tests/test_migration_referentiels.py       | 114 +
backend/tests/test_referentiels_communs.py         | 240 +++
backend/tests/test_referentiels_forme.py           | 141 +++
backend/tests/test_referentiels_relations.py       | 133 +++
docs/CONTRAT-API.md                                |  45 +-
docs/REPRISE.md                                    |  73 +-
```

## Ce qui a été fait, et pourquoi

Livraison de la **section 5 du contrat d'API** (`docs/CONTRAT-API.md`), annoncée en
v1.2 le 20/08 **avant écriture** : six référentiels (machines, cylindres, matières,
outils, clients, options), chacun avec `GET` liste paginée · `GET /{id}` · `POST` ·
`PUT /{id}` · `DELETE /{id}`.

Décision structurante : **un seul routeur CRUD générique instancié six fois**
(`app/routers/referentiels.py`), ce qui est propre à chaque ressource étant déclaré
dans une dataclass `Ressource`. Écarté : six routeurs séparés.

Autres décisions : les gardes (`exiger_session`, `interdire_ecriture_demo`) sont
portées par le **routeur** et non par chaque endpoint ; l'unicité est tranchée par la
**contrainte SQL** (`IntegrityError`) et non par une lecture préalable ; la question
« qui me référence ? » est centralisée dans `est_reference()` /
`app/services/referentiels.py`.

⚠️ **Contexte à connaître** : ce code a été écrit dans une session configurée avec un
profil de règles différent de celui du projet. Il a été conçu, implémenté et validé
par **un seul agent** — les commentaires du code ne sont pas des preuves.

## Zones sensibles touchées

Base · **migrations** (une nouvelle, `49e79c0d2b7a`, aller-retour à vérifier) ·
données persistantes · **API** (contrat v1.2, section 5) · **règles métier**
(unicité, `reference_utilisee`).

## Tests

Commande : `python -m pytest -q` dans `backend/`   Résultat : **221 passés, 0 échoué** (mesuré le 16/09/2026 sur `58a6712`)
CI GitHub sur la PR : `build` **pass**, `test` **pass**.

Un banc de mutations a été joué (7 mutations, 6 rouges). **Non couvert, et déclaré
comme tel** : retirer `.order_by(id)` du routeur ne fait rougir aucun test — sur
SQLite l'ordre naturel coïncide avec l'ordre des identifiants. Le test n'attrape
qu'un ordre explicite *faux*.

Autres zones non couvertes : aucun test de charge ni de volumétrie ; aucun test de
concurrence (deux écritures simultanées sur la même clé) ; la borne de pagination est
testée à 200/201 mais pas au-delà ; le comportement sous PostgreSQL n'est pas testé
(le projet ne cible que SQLite).

## Ce sur quoi je veux ton avis en priorité

1. **Le contrat est-il respecté à la lettre ?** Section 5 de `docs/CONTRAT-API.md`
   contre les JSON réellement rendus : clés exactes, **types chaîne des décimaux**,
   champs nullables, enveloppe `{elements, total}`, codes HTTP et codes d'erreur
   (`deja_existant`, `reference_utilisee`, `introuvable`, `payload_invalide`,
   `session_absente`, `mode_demo_lecture_seule`).

2. **Les « précisions » ajoutées au contrat** par cette session (journal des
   changements v1.2, et en-tête de la section 5) : sont-ce vraiment des précisions,
   ou l'une d'elles **change-t-elle la forme** pour un front déjà écrit contre la v1.2
   annoncée ? En particulier : `PUT` en remplacement complet, clé étrangère inconnue
   en 422, champ inconnu en 422, décimaux normalisés à l'écriture, nullabilité de
   `date_inventaire` / `contact` / `email` / `telephone`.

3. **`est_reference()` et le dictionnaire `LIENS`**
   (`app/services/referentiels.py`) : la suppression refusée couvre-t-elle bien
   machine → cylindre **et** cylindre → outil ? Le point d'extension pour les devis
   (lot 2c) est-il réellement **unique**, ou existe-t-il un chemin de suppression qui
   ne passe pas par là ?

4. **`PUT /{id}` en remplacement complet** sur les référentiels : la sémantique est-elle
   cohérente et sans perte de données ? (Le `PUT` **partiel** des paramètres de coûts
   arrive en PR #13 : les deux sémantiques cohabiteront dans la même API.)

5. **`order_by(id)` sur les listes paginées** : la mutation qui le retire reste verte
   sur SQLite. Existe-t-il un cas où l'ordre naturel diverge de l'ordre des
   identifiants — suppression puis réinsertion, réutilisation de `rowid`, `VACUUM`,
   `WITHOUT ROWID` ? Si oui, la pagination saute-t-elle ou répète-t-elle des éléments ?

6. **Migration `49e79c0d2b7a`** : le `downgrade` est-il **réellement réversible**, et
   pas seulement l'`upgrade` ? Index, contraintes d'unicité et clés étrangères
   reviennent-ils à l'identique après `upgrade → downgrade → upgrade` ?

7. **`_commettre()`** (`app/routers/referentiels.py`) : l'unicité est tranchée par
   `IntegrityError`, puis une relecture nomme le champ fautif. Si cette relecture ne
   trouve rien, l'exception est **relancée** (donc 500). Ce chemin est-il atteignable
   autrement que par une course, et le 500 est-il le bon comportement ?

## Ce que je ne veux PAS voir toucher

- `backend/app/moteur/` et les **montants dorés** — zone gelée, aucune retouche.
- `frontend/`, `deploy/`.
- Refactoring d'élégance, renommages, réorganisation de fichiers.
- **Le choix du routeur générique** : on juge ce qu'il *fait*, pas s'il aurait fallu
  écrire six routeurs.

## Attendu

Audit **EN LECTURE SEULE**. Un constat = gravité (CRITIQUE / ÉLEVÉ / MOYEN / FAIBLE /
OPTIONNEL), fichier, preuve ou raisonnement, impact, correction recommandée, risque de
la correction. Preuve insuffisante → « À confirmer ».

Priorité : exactitude métier > intégrité des données > stabilité > sécurité >
simplicité > maintenabilité > élégance.
