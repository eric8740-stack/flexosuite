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

        Consequence assumee : **vider les donnees remet le bareme en neutre.**
        C'est voulu — un bareme vide n'est plus calibre, et le front doit le
        dire, sinon il presenterait des scores indicatifs comme des scores
        regles.
        """
        donnees = self.donnees or {}
        return not any(bool(valeur) for valeur in donnees.values())
