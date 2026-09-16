# -*- coding: utf-8 -*-
"""Les quatre baremes — livres NEUTRES, calibres ensuite.

`neutre` vaut vrai tant que le bareme n'a pas ete calibre, et le front doit le
**dire** : les scores sont alors indicatifs. Presenter un score indicatif comme
un score regle, c'est faire prendre une decision de prix sur un chiffre qui ne
veut rien dire.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session as SessionSQL

from app import erreurs
from app.database import get_db
from app.dependances import exiger_session, interdire_ecriture_demo
from app.models import TYPES_BAREMES, Bareme, Machine
from app.schemas.enveloppe import Page
from app.schemas.parametres import BaremeEcriture, BaremePublic
from app.services.baremes import assurer_baremes

router = APIRouter(
    prefix="/baremes",
    tags=["baremes"],
    dependencies=[Depends(exiger_session), Depends(interdire_ecriture_demo)],
)

# L'ordre du contrat, qui n'est pas l'ordre alphabetique. Il est trie en Python
# sur quatre lignes plutot qu'en SQL : un `ORDER BY` ne saurait pas le rendre
# sans une colonne de rang, et une colonne de rang pour quatre lignes fixes
# serait une table de plus a maintenir.
ORDRE_CONTRAT = [code for code, _ in TYPES_BAREMES]


def _valider_machines(db: SessionSQL, machines_ids: list[int]) -> None:
    """Une liste VIDE signifie « toutes les machines » — elle est donc valide.

    Un identifiant qui ne designe rien, en revanche, rendrait le bareme
    silencieusement inapplicable : il serait restreint a une machine qui
    n'existe pas, et personne ne verrait pourquoi les scores ne bougent plus.
    """
    for identifiant in machines_ids:
        if db.get(Machine, identifiant) is None:
            raise erreurs.payload_invalide(
                f"machines_ids (aucune machine ne porte l'identifiant {identifiant})"
            )


@router.get("", response_model=Page[BaremePublic])
def lister(db: SessionSQL = Depends(get_db)) -> Page[BaremePublic]:
    """Les quatre, toujours — crees a la volee s'ils manquent.

    L'enveloppe de liste est celle de partout, mais **sans pagination** : quatre
    types fixes ne paginent pas. La forme reste identique pour que le front
    n'ait qu'une seule lecture de liste a ecrire.
    """
    assurer_baremes(db)
    baremes = db.execute(select(Bareme)).scalars().all()
    baremes = sorted(baremes, key=lambda b: ORDRE_CONTRAT.index(b.type))
    return Page[BaremePublic](
        elements=[BaremePublic.model_validate(b) for b in baremes],
        total=len(baremes),
    )


@router.put(
    "/{type_bareme}", response_model=BaremePublic, status_code=status.HTTP_200_OK
)
def calibrer(
    type_bareme: str, entree: BaremeEcriture, db: SessionSQL = Depends(get_db)
) -> BaremePublic:
    """Calibrer : poser des machines, des donnees, une activation.

    `neutre` n'est pas ecrit — il se deduit de `donnees`. Poser des points fait
    donc passer le bareme en calibre, et les retirer le ramene en neutre : la
    question « ce bareme a-t-il ete calibre ? » n'a qu'une seule source.
    """
    assurer_baremes(db)
    bareme = db.get(Bareme, type_bareme)
    if bareme is None:
        raise erreurs.introuvable("Ce bareme")

    _valider_machines(db, entree.machines_ids)
    bareme.machines_ids = entree.machines_ids
    bareme.donnees = entree.donnees
    bareme.actif = entree.actif
    db.commit()
    db.refresh(bareme)
    return BaremePublic.model_validate(bareme)
