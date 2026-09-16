# -*- coding: utf-8 -*-
"""Les decimaux du contrat : ils entrent en `Decimal`, ils sortent en CHAINE.

> « Montants : serialises en **chaine** (`"1777.00"`), jamais en nombre
> flottant. Le front ne fait **aucun calcul monetaire** : il affiche. »

Deux choses se passent ici, et les deux comptent :

1. **La quantification a l'ENTREE.** Le contrat montre `"320.00"` et
   `"0.5000"` : ce ne sont pas des exemples decoratifs, c'est la forme que le
   front recoit. Normaliser a l'ecriture — et non a la lecture — garantit que
   ce qui est relu est exactement ce qui a ete range. Quantifier a la sortie
   ferait dire a l'API deux choses differentes selon le chemin emprunte.
2. **La serialisation en chaine a la SORTIE**, en python comme en JSON, pour
   qu'un test qui lit l'objet et un front qui lit le JSON voient la meme chose.

⚠️ Ceci ne concerne QUE les referentiels et les parametres, c'est-a-dire des
valeurs saisies par l'imprimeur. **Le moteur n'est pas concerne** : la ou les
montants dores tombent au centime, l'arrondi se reproduit poste par poste et ne
se normalise pas (cf. `docs/SPEC-METIER.md`, § 3 bis).
"""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

# Le contrat montre deux precisions, et une seule raison de les distinguer :
# au m2, la troisieme et la quatrieme decimale pesent sur un tirage de
# plusieurs milliers de metres.
DECIMALES_COURANTES = 2
DECIMALES_PRIX_M2 = 4


def _quantifier(nb_decimales: int):
    exposant = Decimal(1).scaleb(-nb_decimales)

    def valider(valeur: Decimal) -> Decimal:
        try:
            # ROUND_HALF_UP explicite : le defaut de Python est HALF_EVEN, qui
            # arrondit 0,125 a 0,12. Personne dans un atelier n'attend ca d'une
            # saisie de tarif.
            return valeur.quantize(exposant, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("nombre hors bornes") from exc

    return valider


Decimal2 = Annotated[
    Decimal,
    AfterValidator(_quantifier(DECIMALES_COURANTES)),
    PlainSerializer(str, return_type=str),
]

Decimal4 = Annotated[
    Decimal,
    AfterValidator(_quantifier(DECIMALES_PRIX_M2)),
    PlainSerializer(str, return_type=str),
]
