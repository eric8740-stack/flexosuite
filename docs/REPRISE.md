# Reprise — où en est FlexoSuite v2

> État **réel**, pas l'intention. À relire en premier au démarrage de toute
> session, avec `docs/PLAN.md`. `git fetch -p` avant tout état git.

## En-tête

- **Date** : 2026-08-20
- **Lot en cours** : **0a — cahier de recette métier** (`docs/SPEC-METIER.md`)
- **Porte G0** : ❌ **pas franchie**. Les formules des 7 postes sont extraites et
  le premier cas de référence tombe au centime, mais **la chaîne de pose ne l'est
  pas** — voir le § 7 de la spec. Tant qu'il n'est pas vide, on n'écrit pas de
  moteur.
- **Qui tient quoi** : une seule instance (**CC1, backend**). `docs/`, `deploy/`
  et `tests/` lui appartiennent. **CC2 n'est pas démarré** et n'a rien à faire
  tant que le top départ n'est pas donné.

## Fait

- **Dépôt créé**, documentation et garde-fou de confidentialité. Aucun code
  applicatif.
- **`docs/SPEC-METIER.md`** — les formules des 7 postes de coût, les invariants,
  et le **jeu doré** fabriqué :
  - paramètres ronds et manifestement fictifs (« Atelier Démo ») ;
  - passés dans l'ancien moteur en local, avec la **structure** des payloads de
    référence ;
  - premier cas de référence : **1 777,00 € HT**, recontrôlé à la main poste par
    poste.
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

**La chaîne de pose** — c'est ce qui manque pour franchir G0. Comment on passe du
format d'étiquette et du cylindre au couple (poses en laize, poses en développé),
puis aux laizes utile et papier et au métrage. Avec la règle du bord et le
plafonnement. Les deux autres cas de référence en dépendent : leur structure est
figée, leurs montants dorés ne sont pas encore produits.

Ensuite : les 8 sens d'enroulement, la règle silhouette, le « format approchant »,
la structure des 4 barèmes, les développés standard re-sourcés depuis les
catalogues publics, et le modèle de données.
