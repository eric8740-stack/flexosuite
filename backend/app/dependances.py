# -*- coding: utf-8 -*-
"""Les gardes que tout endpoint de donnees porte.

Elles sont ici, en un seul endroit, plutot que recopiees : une garde oubliee sur
un endpoint est un trou, et un trou ne se voit pas a la relecture.

Ordre voulu, et il compte :

1. **installation** — sans compte, rien n'a de sens : 409 `installation_requise`,
   et le front envoie vers l'assistant plutot que d'afficher une page vide.
2. **session** — 401 `session_absente`, le front redirige sans perdre la saisie.
3. **mode demo** — les ecritures repondent 403 `mode_demo_lecture_seule`.
"""
from fastapi import Cookie, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session as SessionSQL

from app import erreurs
from app.config import DEMO_MODE
from app.database import get_db
from app.models import Utilisateur
from app.services import sessions

METHODES_ECRITURE = ("POST", "PUT", "PATCH", "DELETE")


def installation_faite(db: SessionSQL) -> bool:
    return db.execute(select(Utilisateur.id).limit(1)).first() is not None


def exiger_installation(db: SessionSQL = Depends(get_db)) -> None:
    if not installation_faite(db):
        raise erreurs.installation_requise()


def utilisateur_courant(
    db: SessionSQL = Depends(get_db),
    flexosuite_session: str | None = Cookie(default=None),
) -> Utilisateur | None:
    """L'utilisateur de la session, ou `None`. Ne leve jamais."""
    return sessions.utilisateur_du_jeton(db, flexosuite_session)


def exiger_session(
    db: SessionSQL = Depends(get_db),
    flexosuite_session: str | None = Cookie(default=None),
) -> Utilisateur:
    if not installation_faite(db):
        raise erreurs.installation_requise()
    utilisateur = sessions.utilisateur_du_jeton(db, flexosuite_session)
    if utilisateur is None:
        raise erreurs.session_absente()
    return utilisateur


def interdire_ecriture_demo(requete: Request) -> None:
    if DEMO_MODE and requete.method in METHODES_ECRITURE:
        raise erreurs.mode_demo_lecture_seule()
