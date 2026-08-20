"""Modeles du noyau devis.

MONO-TENANT : aucune colonne de portee, aucun scope. Une installation = un
imprimeur.

Tout modele doit etre importe ICI, sinon Alembic ne le voit pas : `env.py`
importe ce paquet, et c'est `Base.metadata` qui sert de reference a
l'autogeneration. Un modele oublie ne produit pas d'erreur — il produit une
migration qui ne cree pas sa table.
"""
from app.models.noyau import (  # noqa: F401
    CHAMPS_CALIBRATION,
    ParametresCouts,
    SessionUtilisateur,
    Utilisateur,
    maintenant,
)

__all__ = [
    "CHAMPS_CALIBRATION",
    "ParametresCouts",
    "SessionUtilisateur",
    "Utilisateur",
    "maintenant",
]
