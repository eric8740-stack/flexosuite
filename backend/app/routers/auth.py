# -*- coding: utf-8 -*-
"""Connexion, deconnexion, « qui suis-je ».

Le front ne lit jamais le jeton : le cookie est `HttpOnly`, et **ne pas pouvoir
le lire est precisement la protection**.
"""
from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as SessionSQL

from app import erreurs, securite
from app.database import get_db
from app.dependances import exiger_session, installation_faite, interdire_ecriture_demo
from app.models import Utilisateur
from app.schemas.noyau import Identifiants, UtilisateurPublic
from app.services import sessions

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/connexion",
    dependencies=[Depends(interdire_ecriture_demo)],
    response_model=UtilisateurPublic,
)
def connexion(
    entree: Identifiants,
    reponse: Response,
    db: SessionSQL = Depends(get_db),
) -> UtilisateurPublic:
    if not installation_faite(db):
        raise erreurs.installation_requise()

    utilisateur = db.execute(
        select(Utilisateur).where(Utilisateur.identifiant == entree.identifiant)
    ).scalar_one_or_none()

    # Le hachage est joue MEME quand l'identifiant est inconnu : sans cela, un
    # identifiant inexistant repondrait bien plus vite qu'un mot de passe faux,
    # et le formulaire deviendrait un verificateur d'identifiants.
    hache = utilisateur.mot_de_passe_hache if utilisateur else _HACHE_LEURRE
    correct = securite.verifier_mot_de_passe(entree.mot_de_passe, hache)

    if utilisateur is None or not correct:
        raise erreurs.identifiants_invalides()

    sessions.ouvrir(db, utilisateur, reponse)
    return UtilisateurPublic(identifiant=utilisateur.identifiant, role=utilisateur.role)


@router.post("/deconnexion", status_code=status.HTTP_204_NO_CONTENT)
def deconnexion(
    reponse: Response,
    db: SessionSQL = Depends(get_db),
    flexosuite_session: str | None = Cookie(default=None),
) -> Response:
    """Revoque la session **en base**, pas seulement le cookie.

    Pas de garde de session ici : se deconnecter avec une session deja expiree
    doit reussir. Renvoyer 401 a quelqu'un qui veut partir n'a aucun sens.
    """
    sessions.revoquer(db, flexosuite_session, reponse)
    reponse.status_code = status.HTTP_204_NO_CONTENT
    return reponse


@router.get("/moi", response_model=UtilisateurPublic)
def moi(utilisateur: Utilisateur = Depends(exiger_session)) -> UtilisateurPublic:
    return UtilisateurPublic(identifiant=utilisateur.identifiant, role=utilisateur.role)


# Hache d'un mot de passe qui n'ouvre aucun compte : il ne sert qu'a faire
# passer le meme temps de calcul dans les deux branches.
_HACHE_LEURRE = securite.hacher_mot_de_passe(securite.nouveau_jeton())
