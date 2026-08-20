# Reprise — où en est FlexoSuite v2

> État **réel**, pas l'intention. À relire en premier au démarrage de toute
> session, avec `docs/PLAN.md`. `git fetch -p` avant tout état git.

## En-tête

- **Date** : 2026-08-20
- **Lot en cours** : **lot 1 terminé — prochain : lot 2, données et API**
- **Portes G0, G1 et G2** : ✅ **franchies** (détail et critères dans
  `docs/PLAN.md`).
- **Qui tient quoi** : **CC1** tient `backend/`, `docs/` et `deploy/`. **CC2 est
  démarré** sur `frontend/` — le top départ a été donné le 20/08.
  ⚠️ `docs/CONTRAT-API.md` **ne bouge plus sans annonce**, et le backend est
  livré **avant** le front à chaque évolution.

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

## Prochaine étape

**Lot 2 — données et API.** Modèle mono-tenant, migrations Alembic, endpoints du
contrat, auth sur le patron de livraison. **Ce lot touche `docs/CONTRAT-API.md`**
— l'annoncer à CC2 avant, et livrer le backend en premier.

Reste aussi au moteur : l'**optimiseur** qui choisit entre configurations. Il a
besoin des barèmes, donc du lot 2.
