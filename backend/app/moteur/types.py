# -*- coding: utf-8 -*-
"""Types du moteur — purs, sans base de donnees.

Le moteur ne connait ni SQLAlchemy ni FastAPI : il prend des valeurs, il rend
des valeurs. C'est ce qui permet de le tester contre les montants dores sans
monter la moindre infrastructure.

⚠️ Aucun champ tarifaire ne porte de valeur par defaut. L'application se livre
a ZERO TARIF : un defaut ici, ce serait livrer les tarifs de quelqu'un d'autre.
"""
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class ParametresCouts:
    """Ce que la calibration produit chez l'imprimeur."""

    marge_standard_pct: Decimal          # en POURCENTAGE (0-100), pas en fraction
    cout_exploitation_machine_eur_h: Decimal
    cout_operateur_eur_h: Decimal
    marge_confort_roulage_mm: int
    cliche_prix_couleur_eur: Decimal
    outil_base_eur: Decimal
    outil_par_trace_eur: Decimal
    surcout_forme_speciale_facteur: Decimal   # multiplicateur direct : 1,50 = x1,50
    calage_forfait_eur: Decimal
    finitions_prix_m2_eur: Decimal


@dataclass(frozen=True)
class Matiere:
    grammage_g_m2: Decimal
    prix_m2_eur: Decimal

    @property
    def prix_kg_eur(self) -> Decimal:
        """Le metier raisonne au kilo (les bobines se pesent), les fournisseurs
        facturent au m2. La division n'est PAS arrondie : elle ne tombe pas
        juste, et arrondir ici deplacerait le total de plusieurs centimes."""
        return self.prix_m2_eur * Decimal(1000) / self.grammage_g_m2


@dataclass(frozen=True)
class Machine:
    nom: str
    laize_utile_mm: Decimal
    vitesse_moyenne_m_h: int      # SEUL driver de vitesse
    duree_calage_h: Decimal


@dataclass(frozen=True)
class TarifEncre:
    prix_kg_eur: Decimal
    ratio_g_m2_couleur: Decimal


@dataclass(frozen=True)
class EntreeChiffrage:
    """Un lot chiffrable. La geometrie est deja resolue (cf. `moteur.geometrie`)."""

    matiere: Matiere
    machine: Machine
    laize_utile_mm: Decimal
    ml_total: int
    couleurs_par_type: dict[str, int]
    tarifs_encre: dict[str, TarifEncre]
    laize_papier_mm: Decimal | None = None
    forfaits_sous_traitance: list[Decimal] = field(default_factory=list)
    outil_existant: bool = True
    nb_traces: int = 1
    forme_speciale: bool = False
    heures_dossier_override: Decimal | None = None
    # Porte PAR LOT. Ignore sur le premier lot : son calage est inclus.
    changement_outil_cliche: bool = False


@dataclass(frozen=True)
class PosteCout:
    numero: int
    libelle: str
    montant_eur: Decimal
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ResultatChiffrage:
    postes: list[PosteCout]
    cout_revient_eur: Decimal
    marge_pct: Decimal
    coefficient: Decimal
    prix_vente_ht_eur: Decimal
    nb_calages: int = 1
    calage_mutualise_eur: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class ResultatMultiLots:
    lots: list[ResultatChiffrage]
    cout_revient_eur: Decimal
    prix_vente_ht_eur: Decimal
    nb_calages: int
