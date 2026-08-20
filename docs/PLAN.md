# Plan — FlexoSuite v2

> Les lots et leurs **critères de sortie**, cochés au fur et à mesure. Le plan
> détaillé et les pièges vivent dans `~/.claude/handoffs/PROMPT-CC-FLEXOSUITE-LOT0.md` ;
> ici on suit l'avancement.
>
> **Une porte ne se franchit pas « en attendant ».**

## Lot 0a — Cahier de recette métier

`docs/SPEC-METIER.md`, extrait en lecture seule de `devis-flexo`.

- [x] La **structure** des payloads de référence (géométrie, quantités, options)
- [x] Les formules des 7 postes P1–P7, et **où chaque paramètre se lit**
- [x] Le **jeu doré** fabriqué : paramètres ronds et fictifs, passés dans
      l'ancien moteur → 1er cas de référence à **1 777,00 € HT**
- [x] Garde-fou de confidentialité vert (`tests/test_confidentialite_livraison.py`)
- [x] **La chaîne de pose** (format + cylindre → poses → laizes → métrage)
- [x] Règle du bord et plafonnement à la laize utile
- [x] Les 8 sens d'enroulement
- [x] Règle silhouette
- [x] Logique du « format approchant »
- [x] **Structure** des 4 barèmes — la forme des courbes, jamais des valeurs
      réglées sur un parc existant ; livrés en mode neutre puis calibrés
- [ ] Développés standard de cylindres — catalogue à re-sourcer (non bloquant)
- [x] Modèle de données du noyau devis, sans multi-tenant
- [x] Montants dorés multi-lots + les 3 invariants de calage

> **🟢 Porte G0 — FRANCHIE.** La spec suffit à écrire le moteur sans rouvrir
> l'ancien dépôt et sans un chiffre d'atelier réel. Reste hors chemin critique :
> un catalogue de développés à re-sourcer, et les courbes de barèmes qui ne se
> reprennent pas par construction.

## Lot 0b — Dépôt et squelette

- [x] Dépôt `eric8740-stack/flexosuite` public, poussé
- [x] `docs/REPRISE.md` et `docs/PLAN.md` dès le premier commit
- [x] `CLAUDE.md` du projet
- [x] Arborescence copiée du patron de livraison (backend FastAPI + Alembic +
      SQLite, front Next en export statique conditionnel, `deploy/windows/`)
- [x] CI `build` + `test` — le job `build` refuse route API Next, middleware et
      server action ; le job `test` vérifie aussi l'unicité de la tête Alembic
- [x] Protection de branche sur `main`, les deux checks requis
- [x] `docs/CONTRAT-API.md` v0

> **🟢 Porte G1 — FRANCHIE le 20/08/2026.** Package de 22,7 Mo assemblé, dézippé
> sur un dossier propre, `installer.bat` puis démarrage : la page **et** l'API
> répondent sur **un seul port en écoute**, base et journaux créés dans
> `%ProgramData%\FlexoSuite`. Les deux garde-fous du build ont été exercés —
> imports du Python embarqué vérifiés, aucun chemin interne au-delà de
> 150 caractères.

## Lot 1 — Moteur ✅

Géométrie, chaîne de pose, 8 sens d'enroulement, coûts P1–P7. **Pur, sans base de
données.** Écrit en **TDD** : les montants dorés sont passés en test **avant**
l'implémentation.

- [x] `moteur/types.py` — aucun champ tarifaire ne porte de valeur par défaut
- [x] `moteur/couts.py` — les 7 postes, **arrondi reproduit poste par poste**
- [x] `moteur/geometrie.py` — la chaîne de pose en fonctions pures
- [x] `moteur/sens.py` — les 8 sens et le piège des paires
- [x] Jeu doré dans un **module de fixtures unique**, garde-fou recalé dessus

> **🟢 Porte G2 — FRANCHIE le 20/08/2026.** **40 tests verts**, dont les cinq
> montants dorés et les trois invariants de calage. Chaque poste est vérifié
> **séparément** : un total juste par compensation de deux erreurs resterait
> invisible.

**Reste au moteur, pour plus tard** : l'optimiseur qui *choisit* entre
configurations (score, coefficients de vitesse et de gâche cumulés) — il a besoin
des barèmes, donc du lot 2.

## Lot 2 — Données et API

Modèle **mono-tenant** (`Machine` en table unique, `vitesse_moyenne_m_h` seul
driver de vitesse ; matières, outils, clients, devis et lots, paramètres de
coûts). API FastAPI. Auth sur le patron trésorerie — hachage + révocation des
sessions, **pas de JWT réinventé**. Migrations Alembic.

- Critère : un devis complet se crée et se rejoue par l'API ; migrations vertes.

> **🟡 Contrat d'API gelé** dans `docs/CONTRAT-API.md` **avant** que CC2 parte.
> Quand il bouge, le **backend est livré en premier** — l'inverse envoie le front
> en 422.

## Lot 3 — Front

Optimisation = **point d'entrée unique**, panneau Paramètres.

- Critère : `npm run build` en export statique passe, **zéro** route API Next,
  **zéro** middleware, **zéro** server action ; servi par le backend en mono-port.

## Lot 4 — Démo publique

`flexo.apppreview.fr` sur le VPS Hostinger `hermes-vps`, `deploy/update.sh`,
seed **100 % fictif**, **mode démo en lecture seule**.

- ⚠️ Prérequis **action d'Eric** : enregistrement **A** du sous-domaine vers le
  VPS, sinon Caddy n'émet pas le certificat.
- Critère : HTTPS vert, aucune donnée réelle, écriture impossible.

## Lot 5 — Package client

Installation idempotente, démarrage, mise à jour sans perte, service au boot,
**réinitialisation du mot de passe administrateur**, `README.txt` technicien.

- ⚠️ Le script de réinitialisation **n'existe pas** dans le squelette trésorerie.
  C'est une anomalie relevée le 20/08/2026 : ne pas reproduire le manque.
- Critère : zip dézippé et installé **pour de vrai** sur un poste propre, hors
  ligne.
