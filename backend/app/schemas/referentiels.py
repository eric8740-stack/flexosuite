# -*- coding: utf-8 -*-
"""La forme exacte des six referentiels — section 5 du contrat.

Les noms de champs sont ceux du contrat, **en francais**. Un champ renomme ici
est un front casse : c'est le contrat qui fait loi, pas la commodite du modele.

Deux conventions valent pour les six :

- **`extra="forbid"` en ecriture.** Un champ inconnu envoye par le front est une
  faute de frappe ou un contrat mal lu : le signaler en 422 vaut mieux que de
  l'ignorer en silence, ou que de le ranger dans une colonne qui n'existe pas.
- **`XxxPublic` herite de `XxxEcriture`** et n'ajoute que `id`. Ce n'est pas de
  l'economie de lignes : c'est la garantie qu'une divergence entre ce qu'on
  accepte et ce qu'on rend soit IMPOSSIBLE a introduire par distraction.
  L'ordre des cles change (`id` en dernier) — un objet JSON n'est pas ordonne,
  et aucun front n'en depend.
"""
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.decimaux import Decimal2, Decimal4

ECRITURE = ConfigDict(extra="forbid")
LECTURE = ConfigDict(extra="forbid", from_attributes=True)


class MachineEcriture(BaseModel):
    model_config = ECRITURE

    nom: str = Field(min_length=1, max_length=120)
    laize_utile_mm: Decimal2 = Field(gt=0)
    laize_maxi_mm: Decimal2 = Field(gt=0)
    # Le SEUL driver de vitesse du devis. Aucun autre champ de cadence
    # n'existe, et aucun front n'en calcule un.
    vitesse_moyenne_m_h: int = Field(gt=0)
    duree_calage_h: Decimal2 = Field(ge=0)
    nb_groupes_couleurs: int = Field(ge=0)
    modules: list[str] = Field(default_factory=list)
    diametre_bobine_maxi_mm: Decimal2 = Field(gt=0)
    temps_changement_bobine_h: Decimal2 = Field(ge=0)
    actif: bool = True


class MachinePublic(MachineEcriture):
    model_config = LECTURE

    id: int


class CylindreEcriture(BaseModel):
    model_config = ECRITURE

    developpe_mm: Decimal2 = Field(gt=0)
    # Facultatif, et ce n'est PAS un oubli : un pas de 3,175 mm ne redonne pas
    # un developpe rond, et un parc reel n'a pas toujours l'information. C'est
    # `developpe_mm` qui fait foi.
    nb_dents: int | None = Field(default=None, gt=0)
    repere_machine: str = Field(min_length=1, max_length=32)
    nb_porte_cliches: int = Field(ge=0)
    machine_id: int
    date_inventaire: date | None = None
    actif: bool = True


class CylindrePublic(CylindreEcriture):
    model_config = LECTURE

    id: int


class MatiereEcriture(BaseModel):
    model_config = ECRITURE

    nom: str = Field(min_length=1, max_length=120)
    grammage_g_m2: Decimal2 = Field(gt=0)
    prix_m2_eur: Decimal4 = Field(ge=0)
    # ⚠️ Obligatoire, sans defaut : le diametre de bobine se calcule dessus.
    # Une epaisseur inventee donne un metrage par bobine faux, donc un devis
    # faux — et un devis faux se decouvre chez le client.
    epaisseur_reelle_micron: int = Field(gt=0)
    actif: bool = True


class MatierePublic(MatiereEcriture):
    model_config = LECTURE

    id: int


class OutilEcriture(BaseModel):
    model_config = ECRITURE

    reference: str = Field(min_length=1, max_length=64)
    largeur_mm: Decimal2 = Field(gt=0)
    hauteur_mm: Decimal2 = Field(gt=0)
    nb_poses_laize: int = Field(gt=0)
    nb_poses_developpe: int = Field(gt=0)
    forme_speciale: bool = False
    cylindre_id: int
    actif: bool = True


class OutilPublic(OutilEcriture):
    model_config = LECTURE

    id: int


class ClientEcriture(BaseModel):
    model_config = ECRITURE

    nom: str = Field(min_length=1, max_length=160)
    contact: str | None = Field(default=None, max_length=160)
    # Chaine libre, PAS un `EmailStr`. Deux raisons : le carnet d'adresses d'un
    # atelier contient des choses comme « voir le service achats », et valider
    # le format exigerait une dependance de plus dans un Python embarque qui
    # part hors ligne chez le client.
    email: str | None = Field(default=None, max_length=255)
    telephone: str | None = Field(default=None, max_length=32)
    # Contrainte de la machine de pose DU CLIENT : une donnee de lui, pas de
    # l'imprimeur, et elle contraint l'optimisation.
    intervalle_dev_min_mm: Decimal2 = Field(ge=0)
    actif: bool = True


class ClientPublic(ClientEcriture):
    model_config = LECTURE

    id: int


class Tarification(BaseModel):
    """`{type, montant_eur}` — la seule structure imbriquee des referentiels."""

    model_config = ECRITURE

    # `type` porte le nom du contrat, qui masque une primitive Python. Le
    # contrat fait loi : le renommer casserait le front pour une question de
    # confort de lecture.
    type: Literal["forfait", "m2", "mille"]
    montant_eur: Decimal2 = Field(ge=0)


class OptionEcriture(BaseModel):
    model_config = ECRITURE

    code: str = Field(min_length=1, max_length=64)
    libelle: str = Field(min_length=1, max_length=160)
    # Filtre DUR avec `modules_requis` : une machine qui ne les a pas est
    # ecartee, elle n'est pas penalisee.
    groupes_couleurs_requis: int = Field(default=0, ge=0)
    modules_requis: list[str] = Field(default_factory=list)
    # Impacts de production, cumules MULTIPLICATIVEMENT entre options : un
    # coefficient nul annulerait la vitesse de toute la configuration.
    coefficient_vitesse: Decimal2 = Field(gt=0)
    coefficient_gache: Decimal2 = Field(gt=0)
    temps_calage_ajoute_h: Decimal2 = Field(ge=0)
    tarification: Tarification
    silhouette_automatique: bool = False
    actif: bool = True


class OptionPublic(OptionEcriture):
    model_config = LECTURE

    id: int
