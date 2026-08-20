# -*- coding: utf-8 -*-
"""Assistant d'installation — le premier demarrage, et une seule fois.

`POST /api/installation` cree le compte administrateur ET la ligne de parametres
de couts. Cette ligne part **vide de tarifs**, avec la seule marge : livrer les
tarifs d'un autre atelier produirait des devis faux.

Il ne se rejoue pas. Un assistant rejouable serait une porte d'entree : n'importe
qui pourrait recreer un compte sur une installation en service.
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session as SessionSQL

from app import erreurs, securite
from app.database import get_db
from app.dependances import installation_faite, interdire_ecriture_demo
from app.models import ParametresCouts, Utilisateur
from app.schemas.noyau import Identifiants, UtilisateurPublic
from app.services import sessions

router = APIRouter(tags=["installation"])

# Decision COMMERCIALE, pas un tarif — d'ou sa presence alors que tout le reste
# part vide. Confirmee explicitement par l'imprimeur a l'installation.
MARGE_PAR_DEFAUT_PCT = Decimal("30.00")


@router.post(
    "/installation",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(interdire_ecriture_demo)],
    response_model=UtilisateurPublic,
)
def installer(
    entree: Identifiants,
    reponse: Response,
    db: SessionSQL = Depends(get_db),
) -> UtilisateurPublic:
    if installation_faite(db):
        raise erreurs.installation_deja_faite()

    utilisateur = Utilisateur(
        identifiant=entree.identifiant,
        mot_de_passe_hache=securite.hacher_mot_de_passe(entree.mot_de_passe),
        role="administrateur",
    )
    db.add(utilisateur)
    db.add(ParametresCouts(id=1, marge_standard_pct=MARGE_PAR_DEFAUT_PCT))
    db.commit()
    db.refresh(utilisateur)

    # Session ouverte dans la foulee : faire ressaisir le mot de passe qu'on
    # vient de choisir n'apporte rien.
    sessions.ouvrir(db, utilisateur, reponse)
    return UtilisateurPublic(identifiant=utilisateur.identifiant, role=utilisateur.role)
