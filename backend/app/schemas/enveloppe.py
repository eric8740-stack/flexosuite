# -*- coding: utf-8 -*-
"""L'enveloppe de liste — **la meme partout**, devis compris au lot 2c.

Elle vivait dans le routeur des referentiels. Elle est remontee ici au lot 2b-2,
quand les baremes en ont eu besoin a leur tour : une enveloppe definie dans un
routeur et recopiee dans un autre est une enveloppe qui finira par differer d'un
endpoint a l'autre, et le front devrait alors ecrire deux lectures de liste.
"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """`{ "elements": [...], "total": n }` — jamais un tableau nu.

    Une seule forme de liste a ecrire cote front, et une ressource qui grossit
    ne casse rien le jour ou elle depasse un ecran.
    """

    elements: list[T]
    total: int
