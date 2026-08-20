# Reprise — où en est FlexoSuite v2

> État **réel**, pas l'intention. À relire en premier au démarrage de toute
> session, avec `docs/PLAN.md`. `git fetch -p` avant tout état git.

## En-tête

- **Date** : 2026-08-20
- **Lot en cours** : **0b — dépôt et squelette** (0a terminé)
- **Porte G0** : ✅ **franchie**. La spec suffit à écrire le moteur sans rouvrir
  l'ancien dépôt et sans un chiffre d'atelier réel — § 7 de la spec pour le
  détail de ce qui reste (un catalogue à re-sourcer, et les courbes de barèmes
  qui ne se reprennent pas par construction).
- **Qui tient quoi** : une seule instance (**CC1, backend**). `docs/`, `deploy/`
  et `tests/` lui appartiennent. **CC2 n'est pas démarré** et n'a rien à faire
  tant que le top départ n'est pas donné.

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
    1 587,66 € avec l'atelier non rond) et trois multi-lots (775,74 · 1 301,48 ·
    1 551,48) qui verrouillent la règle du calage ;
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

## Prochaine étape

**Lot 0b — le dépôt et le squelette.** Publier le dépôt distant, copier
l'arborescence du squelette de livraison, poser la CI `build` + `test` et la
protection de branche. **Porte G1** : le zip s'installe sur un poste propre et
sert une page en mono-port, données dans `%ProgramData%\FlexoSuite`.

Puis **lot 1 — le moteur**, en TDD contre les cinq montants dorés et les trois
invariants de calage.
