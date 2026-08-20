# -*- coding: utf-8 -*-
"""LE SEUL module du depot autorise a porter des valeurs chiffrees de tarif.

Tout ce qui suit est **fictif et fabrique**. Ce ne sont les tarifs d'aucun
atelier reel : ils ont ete choisis ronds (atelier A) ou deliberement non ronds
(atelier B), passes dans un moteur valide, et les montants obtenus sont devenus
les references de ce depot.

`tests/test_confidentialite_livraison.py` verifie qu'aucune valeur de tarif
n'existe ailleurs. Si vous avez besoin d'un nombre pour un test, il vient d'ici.

⚠️ Ce n'est PAS le parametrage livre au client : l'application part a zero
tarif, et un assistant de calibration les fait produire chez l'imprimeur.
"""
from decimal import Decimal

from app.moteur.types import Machine, Matiere, ParametresCouts, TarifEncre

# =============================================================================
#  ATELIER DEMO A — tout est rond, pour que les cas se recontrolent a la main
# =============================================================================
PARAMETRES_A = ParametresCouts(
    marge_standard_pct=Decimal("25.00"),
    cout_exploitation_machine_eur_h=Decimal("300.00"),
    cout_operateur_eur_h=Decimal("60.00"),
    marge_confort_roulage_mm=20,
    cliche_prix_couleur_eur=Decimal("40.00"),
    outil_base_eur=Decimal("250.00"),
    outil_par_trace_eur=Decimal("60.00"),
    surcout_forme_speciale_facteur=Decimal("1.50"),
    calage_forfait_eur=Decimal("200.00"),
    finitions_prix_m2_eur=Decimal("0.2000"),
)

# 100 g/m2 a 0,50 EUR/m2 -> 5,00 EUR/kg tout rond
MATIERE_A = Matiere(grammage_g_m2=Decimal("100.0"), prix_m2_eur=Decimal("0.5000"))

MACHINE_A = Machine(
    nom="Presse Demo A",
    laize_utile_mm=Decimal("320.00"),
    vitesse_moyenne_m_h=5000,
    duree_calage_h=Decimal("2.00"),
)

ENCRES_A = {
    "quadri": TarifEncre(prix_kg_eur=Decimal("20.00"), ratio_g_m2_couleur=Decimal("2.000")),
    "pantone": TarifEncre(prix_kg_eur=Decimal("25.00"), ratio_g_m2_couleur=Decimal("2.000")),
}

FORFAIT_ST_A = Decimal("100.00")

# =============================================================================
#  ATELIER DEMO B — rien n'est rond, pour exercer les arrondis
#  Divisions non terminantes voulues : le prix au kilo et le temps de
#  production ne tombent pas juste, et l'arrondi final mord.
# =============================================================================
PARAMETRES_B = ParametresCouts(
    marge_standard_pct=Decimal("27.50"),
    cout_exploitation_machine_eur_h=Decimal("287.45"),
    cout_operateur_eur_h=Decimal("58.90"),
    marge_confort_roulage_mm=15,
    cliche_prix_couleur_eur=Decimal("37.80"),
    outil_base_eur=Decimal("243.70"),
    outil_par_trace_eur=Decimal("57.30"),
    surcout_forme_speciale_facteur=Decimal("1.35"),
    calage_forfait_eur=Decimal("193.60"),
    finitions_prix_m2_eur=Decimal("0.1875"),
)

# 90,5 g/m2 a 0,4275 EUR/m2 -> 4,723756906... EUR/kg (non terminant, c'est le but)
MATIERE_B = Matiere(grammage_g_m2=Decimal("90.5"), prix_m2_eur=Decimal("0.4275"))

MACHINE_B = Machine(
    nom="Presse Demo B",
    laize_utile_mm=Decimal("213.00"),
    vitesse_moyenne_m_h=4730,
    duree_calage_h=Decimal("1.75"),
)

ENCRES_B = {
    "quadri": TarifEncre(prix_kg_eur=Decimal("18.65"), ratio_g_m2_couleur=Decimal("2.150")),
    "pantone": TarifEncre(prix_kg_eur=Decimal("23.40"), ratio_g_m2_couleur=Decimal("2.150")),
}

FORFAIT_ST_B = Decimal("87.35")

# =============================================================================
#  Fixture du cas MULTI-LOTS (atelier A)
# =============================================================================
CYLINDRE_DEVELOPPE_MM = Decimal("300.00")
FORMAT_LARGEUR_MM = Decimal("100")
FORMAT_HAUTEUR_MM = Decimal("80")
QUANTITE_PAR_LOT = 10_000
POSES_LAIZE = 3
POSES_DEV = 2
