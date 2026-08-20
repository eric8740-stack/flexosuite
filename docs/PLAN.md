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

Découpé en trois sous-lots, **backend livré avant le front** à chaque fois :

- [x] **2a — le socle.** `utilisateur`, `session_utilisateur`, `parametres_couts` ;
      migration initiale (aller-retour vérifié) ; installation, connexion,
      déconnexion **révoquée en base**, `GET /api/contexte` complet, contrôle
      d'origine sur les écritures, format d'erreur `{code, detail}` partout.
      `reinitialiser_admin` implémenté et testé sur son comportement réel.
- [ ] **2b — référentiels et paramètres.** ⚠️ **Changement de contrat** : le JSON
      exact de chaque ressource n'y est pas encore. À annoncer à CC2 **avant
      écriture**, dans une PR de documentation séparée.
- [ ] **2c — optimisation, chiffrage, devis.** Le moteur du lot 1 branché sur
      l'API. Les montants dorés restent la référence : aucun ne bouge.

> **🟡 Contrat d'API : v1 annoncée le 20/08**, avant écriture du lot 2. Il porte
> un **journal des changements** et un **état de livraison par section**. Quand il
> bouge : annonce d'abord, **backend livré en premier** — l'inverse envoie le
> front en 422.

## Lot 3 — Front ✅ (livré par CC2, PR #6)

Optimisation = **point d'entrée unique**, aperçu de chiffrage, les 8 sens.

- [x] Socle Tailwind + ESLint, thèmes clair et sombre
- [x] Écran d'optimisation : configurations dans **l'ordre reçu**, moins de trois
      présenté comme normal, outil à fabriquer présenté comme une alternative
- [x] Aperçu de chiffrage : **coefficient**, détail par lot, calage mutualisé
- [x] Les 8 sens, avec le piège des paires traité explicitement
- [x] Export statique vert, servi en mono-port, **aucune URL absolue** dans le bundle
- [ ] Session, redirection au 401, écran d'installation — **volontairement non
      figés** tant que le backend du lot 2 n'est pas livré

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
