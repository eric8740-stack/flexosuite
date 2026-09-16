# -*- coding: utf-8 -*-
"""Les six referentiels de la section 5 du contrat.

MONO-TENANT, comme le noyau : aucune colonne de portee. Une installation = un
imprimeur.

Deux choix valent pour les six tables, et ils viennent du contrat :

- **`actif` plutot que la suppression.** Un element desactive n'est plus propose
  a l'optimisation mais **reste lisible** dans les devis passes. Effacer une
  machine referencee reecrirait l'histoire de devis deja envoyes a des clients —
  et un devis qu'on ne sait plus expliquer est un devis qu'on ne sait plus
  defendre.
- **Les cles etrangeres ne cascadent PAS.** La suppression d'un element
  referencee est refusee par l'application (409 `reference_utilisee`), et la
  contrainte SQLite est la deuxieme serrure : si la garde applicative sautait,
  la base refuserait encore plutot que de laisser des orphelins.
"""
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.types_sql import DecimalTexte, JsonTexte


class Machine(Base):
    """Le parc de presses — **table unique, source de verite**.

    `vitesse_moyenne_m_h` est le SEUL driver de vitesse : il n'existe aucun autre
    champ de cadence, et personne n'en calcule un ailleurs. Deux sources de
    vitesse finiraient par diverger, et le devis prendrait la mauvaise.
    """

    __tablename__ = "machine"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    laize_utile_mm: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    laize_maxi_mm: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    vitesse_moyenne_m_h: Mapped[int] = mapped_column(Integer, nullable=False)
    duree_calage_h: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    nb_groupes_couleurs: Mapped[int] = mapped_column(Integer, nullable=False)
    # Codes libres : ce sont eux que `option.modules_requis` compare.
    modules: Mapped[object] = mapped_column(JsonTexte, nullable=False, default=list)
    diametre_bobine_maxi_mm: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    temps_changement_bobine_h: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Cylindre(Base):
    """Le catalogue de cylindres d'une machine.

    ⚠️ **`developpe_mm` fait foi** : c'est lui, et lui seul, qui entre dans la
    chaine de pose. `nb_dents` est un **repere de catalogue facultatif** — un pas
    de 3,175 mm ne redonne pas un developpe rond, et un parc reel n'a pas
    toujours l'information. Ne jamais recalculer l'un depuis l'autre.
    """

    __tablename__ = "cylindre"
    __table_args__ = (
        # Le repere est celui grave sur la machine : il est unique CHEZ ELLE,
        # pas dans tout l'atelier. Deux presses ont chacune leur « A3 ».
        UniqueConstraint("machine_id", "repere_machine", name="uq_cylindre_machine_repere"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    developpe_mm: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    nb_dents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repere_machine: Mapped[str] = mapped_column(String(32), nullable=False)
    nb_porte_cliches: Mapped[int] = mapped_column(Integer, nullable=False)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machine.id"), nullable=False, index=True)
    date_inventaire: Mapped[date | None] = mapped_column(Date, nullable=True)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Matiere(Base):
    """Les supports.

    ⚠️ `epaisseur_reelle_micron` n'a **pas de valeur par defaut acceptable** : le
    diametre de bobine se calcule dessus. Une epaisseur inventee donne un
    diametre faux, donc un metrage par bobine faux, donc un devis faux. Le champ
    est obligatoire a la creation, et il n'y a pas de repli.
    """

    __tablename__ = "matiere"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    grammage_g_m2: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    # QUATRE decimales : au m2, la troisieme et la quatrieme pesent sur un
    # tirage de plusieurs milliers de metres.
    prix_m2_eur: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    epaisseur_reelle_micron: Mapped[int] = mapped_column(Integer, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Outil(Base):
    """Les outils de decoupe deja fabriques.

    C'est ce catalogue qui rend le « format approchant » possible : reutiliser un
    outil quasi compatible plutot que d'en fabriquer un neuf.
    """

    __tablename__ = "outil"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    largeur_mm: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    hauteur_mm: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    nb_poses_laize: Mapped[int] = mapped_column(Integer, nullable=False)
    nb_poses_developpe: Mapped[int] = mapped_column(Integer, nullable=False)
    forme_speciale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cylindre_id: Mapped[int] = mapped_column(ForeignKey("cylindre.id"), nullable=False, index=True)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Client(Base):
    """Les donneurs d'ordre.

    `intervalle_dev_min_mm` est la contrainte de **sa** machine de pose : c'est
    une donnee du client, pas de l'imprimeur, et elle contraint l'optimisation.
    """

    __tablename__ = "client"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    contact: Mapped[str | None] = mapped_column(String(160), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telephone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intervalle_dev_min_mm: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Option(Base):
    """Les options de production (vernis, microperfo, dorure...).

    Deux familles de champs, et elles ne se melangent pas :

    - `groupes_couleurs_requis` et `modules_requis` sont un **filtre dur** — une
      machine qui ne les a pas est ECARTEE, elle n'est pas penalisee ;
    - `coefficient_vitesse` et `coefficient_gache` sont des impacts de
      production, **cumules multiplicativement** entre options.
    """

    __tablename__ = "option"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    libelle: Mapped[str] = mapped_column(String(160), nullable=False)
    groupes_couleurs_requis: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    modules_requis: Mapped[object] = mapped_column(JsonTexte, nullable=False, default=list)
    coefficient_vitesse: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    coefficient_gache: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    temps_calage_ajoute_h: Mapped[object] = mapped_column(DecimalTexte(16), nullable=False)
    # `{type, montant_eur}` — `type` dans forfait | m2 | mille.
    tarification: Mapped[object] = mapped_column(JsonTexte, nullable=False)
    # Declenche la regle silhouette, qui ORIENTE la recherche de format.
    silhouette_automatique: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
