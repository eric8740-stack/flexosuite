# -*- coding: utf-8 -*-
"""Les 8 sens d'enroulement — convention flexographique officielle.

Trois vues, et une seule ne souffre aucune approximation :

  - VUE PLANCHE : la planche presse, verticale, l'avance vers le bas.
  - VUE VOLUME  : le rouleau en 3D — **seule vue ou se voit la face imprimee**.
  - VUE BOBINE  : la bobine fille deroulee chez le client, horizontale.

⚠️ Les paires (1,5) (2,6) (3,7) (4,8) ont **exactement les memes rotations** en
vue planche et en vue bobine. Seule la face imprimee les distingue. Une
interface qui n'affiche que la planche rend ces sens indiscernables.

Pourquoi c'est critique : la vue planche est celle que lit le poseur de cliches
pour orienter le cliche sur la presse. Fausse -> cliche pose a l'envers ->
tirage entier a jeter.

Rotations horaires, en degres : 0 tete en haut, 90 tete a droite, 180 tete en
bas, 270 tete a gauche.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SensEnroulement:
    numero: int
    libelle: str
    rotation_vue_planche: int
    rotation_vue_bobine: int
    face: str  # "exterieur" ou "interieur"


SENS: dict[int, SensEnroulement] = {
    1: SensEnroulement(1, "0° Extérieur droite avant", 90, 0, "exterieur"),
    2: SensEnroulement(2, "180° Extérieur gauche avant", 270, 180, "exterieur"),
    3: SensEnroulement(3, "270° Extérieur pied avant", 0, 270, "exterieur"),
    4: SensEnroulement(4, "90° Extérieur tête avant", 180, 90, "exterieur"),
    5: SensEnroulement(5, "0° Intérieur droite avant", 90, 0, "interieur"),
    6: SensEnroulement(6, "180° Intérieur gauche avant", 270, 180, "interieur"),
    7: SensEnroulement(7, "270° Intérieur pied avant", 0, 270, "interieur"),
    8: SensEnroulement(8, "90° Intérieur tête avant", 180, 90, "interieur"),
}


def sens(numero: int) -> SensEnroulement:
    """Un sens hors de 1-8 leve une erreur.

    Il n'existe pas de valeur par defaut raisonnable : un sens invente
    orienterait un cliche au hasard.
    """
    if numero not in SENS:
        raise ValueError(f"Sens d'enroulement {numero!r} inconnu — attendu de 1 à 8.")
    return SENS[numero]


def paire_indiscernable(numero: int) -> int:
    """Le sens qui partage les memes rotations, et ne differe que par la face."""
    s = sens(numero)
    return numero + 4 if s.face == "exterieur" else numero - 4
