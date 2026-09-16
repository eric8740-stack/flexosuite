# -*- coding: utf-8 -*-
"""Les quatre baremes de la section 6 du contrat.

**Quatre types fixes, et c'est structurel** : `type` est la cle primaire. Il n'y
a pas d'identifiant de substitution, parce qu'il n'y a rien a identifier d'autre
— le contrat adresse un bareme par `/api/baremes/{type}` et son JSON ne porte
aucun `id`.

⚠️ **Ils sont livres en mode NEUTRE** : coefficients a 1,0, aucune configuration
favorisee. Livrer les courbes reglees sur le parc d'un autre atelier produirait
des scores faux — c'est la meme raison qui fait partir l'application a zero
tarif.
"""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.types_sql import JsonTexte

# Les quatre types, et leur libelle par defaut. L'ordre est celui du contrat.
TYPES_BAREMES: tuple[tuple[str, str], ...] = (
    ("echenillage", "Echenillage"),
    ("effet_banane", "Effet banane"),
    ("confort_roulage", "Confort roulage"),
    ("compensation_laize_dev", "Compensation laize / developpe"),
)

# Ce que porte un bareme qui n'a jamais ete calibre.
DONNEES_NEUTRES: dict = {"points": []}


class Bareme(Base):
    """Un bareme, calibre ou non.

    `machines_ids` vide signifie **toutes les machines** — et non « aucune ».
    C'est le sens du contrat, et il est contre-intuitif : une liste vide qui
    voudrait dire « aucune » rendrait le bareme inerte a l'installation, alors
    qu'il doit s'appliquer partout tant qu'on ne l'a pas restreint.
    """

    __tablename__ = "bareme"

    type: Mapped[str] = mapped_column(String(32), primary_key=True)
    libelle: Mapped[str] = mapped_column(String(80), nullable=False)
    machines_ids: Mapped[object] = mapped_column(JsonTexte, nullable=False, default=list)
    donnees: Mapped[object] = mapped_column(JsonTexte, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    @property
    def neutre(self) -> bool:
        """CALCULE, jamais stocke — comme `calibration_faite` des parametres.

        Un booleen range a cote de la donnee qu'il decrit finit par la
        contredire : il suffit d'un chemin d'ecriture qui oublie de le mettre a
        jour. Ici, la question « ce bareme a-t-il ete calibre ? » n'a qu'une
        seule source : le contenu de `donnees`.

        ⚠️ **Il se lit sur `points`, et sur rien d'autre** — constat 3 de
        l'audit du 16/09/2026. La version precedente demandait « une valeur
        quelconque de `donnees` est-elle vraie ? », et se trompait **dans les
        deux sens**, ce qui a ete mesure :

        - `{"coefficient": 0}` ou `{"actif_courbe": False}` rendaient
          `neutre=True` — une valeur *falsy* passait pour une absence ;
        - `{"points": [], "version": 1}` rendait `neutre=False` — une simple
          **metadonnee** suffisait a faire croire a une calibration, alors
          qu'aucun point n'etait pose.

        Le second sens est le pire : le front cesse alors d'avertir que les
        scores sont indicatifs, et un score indicatif presente comme regle fait
        prendre une decision de prix sur un chiffre qui ne veut rien dire.

        La cause n'etait pas le calcul, c'etait le **contrat** : on deduisait un
        booleen metier affiche a l'utilisateur d'une structure que le contrat ne
        specifiait pas. `donnees` reste libre pour ses metadonnees, mais la
        **courbe** a desormais une forme nommee : `points`. Une clef libre
        n'influence plus `neutre` — c'est ce qui rend le calcul previsible.
        """
        donnees = self.donnees or {}
        if not isinstance(donnees, dict):
            return True
        return not donnees.get("points")
