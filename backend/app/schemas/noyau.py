# -*- coding: utf-8 -*-
"""Installation, session, contexte.

Les noms de champs sont ceux du contrat, **en francais**. Un champ renomme ici
est un front casse : c'est le contrat qui fait loi, pas la commodite du modele.
"""
from pydantic import BaseModel, Field, field_validator


class Identifiants(BaseModel):
    """Entree de l'installation et de la connexion."""

    identifiant: str = Field(min_length=3, max_length=64)
    # 8 caracteres au minimum. Volontairement bas : c'est un poste d'atelier,
    # souvent partage, sur un reseau local. Une exigence de complexite produit
    # surtout des mots de passe ecrits sur un post-it colle a l'ecran.
    mot_de_passe: str = Field(min_length=8, max_length=256)

    @field_validator("identifiant")
    @classmethod
    def _sans_espaces(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("identifiant vide")
        return v


class UtilisateurPublic(BaseModel):
    """Ce que le front a le droit de savoir. Jamais le hache, evidemment."""

    identifiant: str
    role: str


class Contexte(BaseModel):
    """Ce que le front doit savoir AVANT d'afficher quoi que ce soit.

    Les deux drapeaux commandent l'aiguillage, dans cet ordre : sans
    installation il n'y a pas de compte ; sans calibration il n'y a pas de
    tarifs, donc aucun prix affichable.
    """

    mode_demo: bool
    installation_faite: bool
    calibration_faite: bool
    utilisateur: UtilisateurPublic | None
