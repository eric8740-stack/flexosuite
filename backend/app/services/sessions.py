# -*- coding: utf-8 -*-
"""Ouverture, verification et revocation des sessions.

Le contrat fige le cookie ; ce module l'applique. Trois points valent qu'on les
relise avant de toucher quoi que ce soit :

- **`SameSite=Strict` ne casse pas le developpement.** Le port n'entre PAS dans
  la definition de *same-site* : `localhost:3000` et `localhost:8000` sont
  same-site. L'HOTE, lui, compte — `127.0.0.1` et `localhost` sont cross-site.
- **`Secure` est un reglage, pas une constante.** La demo publique est en HTTPS
  et l'exige ; le package client tourne en HTTP sur le reseau de l'imprimerie et
  serait sinon inutilisable. Defaut a vrai : la derogation est explicite.
- **La revocation est en base.** `deconnexion` ecrit `revoquee_le`, elle ne se
  contente pas d'effacer le cookie.
"""
from datetime import timedelta

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.orm import Session as SessionSQL

from app import securite
from app.config import COOKIE_SECURE, SESSION_DUREE_H
from app.models import SessionUtilisateur, Utilisateur, maintenant

NOM_COOKIE = "flexosuite_session"


def ouvrir(db: SessionSQL, utilisateur: Utilisateur, reponse: Response) -> SessionUtilisateur:
    """Cree la session en base et pose le cookie."""
    jeton = securite.nouveau_jeton()
    session = SessionUtilisateur(
        jeton_hache=securite.empreinte_jeton(jeton),
        utilisateur_id=utilisateur.id,
        expire_le=maintenant() + timedelta(hours=SESSION_DUREE_H),
    )
    db.add(session)
    db.commit()

    reponse.set_cookie(
        NOM_COOKIE,
        jeton,
        httponly=True,
        samesite="strict",
        secure=COOKIE_SECURE,
        path="/",
        max_age=SESSION_DUREE_H * 3600,
    )
    return session


def utilisateur_du_jeton(db: SessionSQL, jeton: str | None) -> Utilisateur | None:
    """Rend l'utilisateur d'un jeton **valide**, sinon `None`.

    Valide = existe, non revoquee, non expiree. L'expiration est verifiee en
    Python et non en SQL : les dates sont stockees avec fuseau, et une
    comparaison SQL sur du texte ISO se serait revelee fausse le jour d'un
    changement d'heure.
    """
    if not jeton:
        return None
    session = db.execute(
        select(SessionUtilisateur).where(
            SessionUtilisateur.jeton_hache == securite.empreinte_jeton(jeton)
        )
    ).scalar_one_or_none()
    if session is None or session.revoquee_le is not None:
        return None
    if _aware(session.expire_le) <= maintenant():
        return None
    return session.utilisateur


def revoquer(db: SessionSQL, jeton: str | None, reponse: Response) -> None:
    """Revoque la session **en base**, puis efface le cookie."""
    if jeton:
        session = db.execute(
            select(SessionUtilisateur).where(
                SessionUtilisateur.jeton_hache == securite.empreinte_jeton(jeton)
            )
        ).scalar_one_or_none()
        if session is not None and session.revoquee_le is None:
            session.revoquee_le = maintenant()
            db.commit()
    reponse.delete_cookie(NOM_COOKIE, path="/")


def _aware(valeur):
    """SQLite rend des `datetime` NAIFS meme sur une colonne `timezone=True`.

    Les comparer a un `datetime` conscient leve `TypeError`. On les relit donc
    comme de l'UTC — ce qu'ils sont, puisque `maintenant()` est la seule source
    d'ecriture.
    """
    from datetime import timezone

    return valeur if valeur.tzinfo is not None else valeur.replace(tzinfo=timezone.utc)
