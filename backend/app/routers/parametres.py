# -*- coding: utf-8 -*-
"""Les parametres de couts — le seul `PUT` PARTIEL du contrat.

Partiel parce que ces valeurs s'enregistrent **champ par champ**, au fil de
l'assistant de calibration : l'imprimeur trouve son taux machine un jour, le
prix de ses cliches chez son photograveur la semaine suivante. Exiger le corps
entier obligerait le front a renvoyer des champs qu'il n'a pas, et un champ
manquant effacerait une valeur deja saisie.

Les referentiels, eux, se remplacent en bloc — ils se saisissent dans un
formulaire entier.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session as SessionSQL

from app import erreurs
from app.database import get_db
from app.dependances import exiger_session, interdire_ecriture_demo
from app.models import ParametresCouts
from app.schemas.parametres import ParametresCoutsModification, ParametresCoutsPublic

router = APIRouter(
    prefix="/parametres",
    tags=["parametres"],
    dependencies=[Depends(exiger_session), Depends(interdire_ecriture_demo)],
)


def _parametres(db: SessionSQL) -> ParametresCouts:
    """La ligne unique, posee par l'assistant d'installation.

    Son absence ne devrait pas arriver : `exiger_session` garantit deja qu'une
    installation existe, et l'installation cree cette ligne. Si elle manque
    quand meme, mieux vaut un 404 franc qu'un `None` qui remonterait en 500
    trois lignes plus loin.
    """
    parametres = db.execute(select(ParametresCouts).limit(1)).scalar_one_or_none()
    if parametres is None:
        raise erreurs.introuvable("Les parametres de couts")
    return parametres


@router.get("/couts", response_model=ParametresCoutsPublic)
def lire(db: SessionSQL = Depends(get_db)) -> ParametresCoutsPublic:
    return ParametresCoutsPublic.model_validate(_parametres(db))


@router.put("/couts", response_model=ParametresCoutsPublic)
def modifier(
    entree: ParametresCoutsModification, db: SessionSQL = Depends(get_db)
) -> ParametresCoutsPublic:
    """Seuls les champs ENVOYES changent.

    `champs_modifies()` s'appuie sur `exclude_unset` : un champ absent du corps
    n'est pas « mis a `null` », il n'est pas touche. La distinction est tout
    l'interet du `PUT` partiel — et elle serait perdue avec un `model_dump()`
    ordinaire, qui rendrait les defauts comme s'ils avaient ete envoyes.
    """
    parametres = _parametres(db)
    for champ, valeur in entree.champs_modifies().items():
        setattr(parametres, champ, valeur)
    db.commit()
    db.refresh(parametres)
    return ParametresCoutsPublic.model_validate(parametres)
