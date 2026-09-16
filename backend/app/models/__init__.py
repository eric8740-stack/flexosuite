"""Modeles du noyau devis.

MONO-TENANT : aucune colonne de portee, aucun scope. Une installation = un
imprimeur.

Tout modele doit etre importe ICI, sinon Alembic ne le voit pas : `env.py`
importe ce paquet, et c'est `Base.metadata` qui sert de reference a
l'autogeneration. Un modele oublie ne produit pas d'erreur — il produit une
migration qui ne cree pas sa table.
"""
from app.models.baremes import (  # noqa: F401
    DONNEES_NEUTRES,
    TYPES_BAREMES,
    Bareme,
)
from app.models.noyau import (  # noqa: F401
    CHAMPS_CALIBRATION,
    ParametresCouts,
    SessionUtilisateur,
    Utilisateur,
    maintenant,
)
from app.models.referentiels import (  # noqa: F401
    Client,
    Cylindre,
    Machine,
    Matiere,
    Option,
    Outil,
)

__all__ = [
    "CHAMPS_CALIBRATION",
    "DONNEES_NEUTRES",
    "TYPES_BAREMES",
    "Bareme",
    "Client",
    "Cylindre",
    "Machine",
    "Matiere",
    "Option",
    "Outil",
    "ParametresCouts",
    "SessionUtilisateur",
    "Utilisateur",
    "maintenant",
]
