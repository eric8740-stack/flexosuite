# -*- coding: utf-8 -*-
"""Le point UNIQUE ou se decide qu'un referentiel est encore utilise.

Le contrat refuse la suppression d'un element qui sert ailleurs (409
`reference_utilisee`) et propose la desactivation a la place. La question « qui
me reference ? » se posera pour chaque nouvelle table du lot 2c — devis, lots,
lignes d'options. Si chaque routeur portait sa propre reponse, il suffirait d'en
oublier UNE pour qu'une suppression efface en silence ce qu'un devis envoye a un
client raconte encore.

Elle se pose donc ici, une fois. **Le lot 2c ajoute des entrees a `LIENS`, il
n'ecrit pas de nouvelle fonction.**
"""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session as SessionSQL

from app.models import Cylindre, Machine, Outil


@dataclass(frozen=True)
class Lien:
    """« Un `modele` me designe par sa colonne `colonne`. »"""

    modele: type
    colonne: str
    # Ce que l'utilisateur lira : « un cylindre utilise encore cette machine ».
    libelle: str


LIENS: dict[type, tuple[Lien, ...]] = {
    Machine: (Lien(Cylindre, "machine_id", "un cylindre"),),
    Cylindre: (Lien(Outil, "cylindre_id", "un outil"),),
}


def est_reference(db: SessionSQL, element) -> str | None:
    """Rend le libelle de ce qui reference `element`, ou `None`.

    On s'arrete au PREMIER trouve : le message nomme une raison, pas un
    inventaire. Un deviseur n'a pas besoin de savoir combien d'outils pendent a
    ce cylindre pour comprendre qu'il ne peut pas l'effacer.
    """
    for lien in LIENS.get(type(element), ()):
        colonne = getattr(lien.modele, lien.colonne)
        trouve = db.execute(
            select(lien.modele.id).where(colonne == element.id).limit(1)
        ).first()
        if trouve is not None:
            return lien.libelle
    return None
