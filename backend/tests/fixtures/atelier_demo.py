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

# =============================================================================
#  REFERENTIELS DEMO — les corps exacts de la section 5 du contrat
#
#  Ils vivent ICI et nulle part ailleurs : `vitesse_moyenne_m_h`, `duree_calage_h`
#  et `prix_m2_eur` sont des champs tarifaires, et le garde-fou de
#  confidentialite refuse qu'une de leurs valeurs soit ecrite dans un autre
#  fichier du depot. Les tests importent, ils ne recopient pas.
#
#  Les deux corps a cle etrangere partent SANS elle : c'est le test qui cree la
#  machine ou le cylindre, puis ajoute l'identifiant obtenu.
# =============================================================================
MACHINE_DEMO = {
    "nom": "Presse Demo A",
    "laize_utile_mm": "320.00",
    "laize_maxi_mm": "330.00",
    "vitesse_moyenne_m_h": 5000,
    "duree_calage_h": "2.00",
    "nb_groupes_couleurs": 8,
    "modules": ["vernis", "dorure"],
    "diametre_bobine_maxi_mm": "800.00",
    "temps_changement_bobine_h": "0.25",
    "actif": True,
}

# `nb_dents` a None VOLONTAIREMENT : c'est un repere de catalogue facultatif,
# et le contrat v1.2 l'a rendu nullable. Le cas nul est donc le cas nominal.
CYLINDRE_DEMO = {
    "developpe_mm": "300.00",
    "nb_dents": None,
    "repere_machine": "A3",
    "nb_porte_cliches": 2,
    "date_inventaire": "2026-08-20",
    "actif": True,
}

MATIERE_DEMO = {
    "nom": "Papier Demo 100",
    "grammage_g_m2": "100.00",
    "prix_m2_eur": "0.5000",
    "epaisseur_reelle_micron": 95,
    "actif": True,
}

OUTIL_DEMO = {
    "reference": "OD-2201",
    "largeur_mm": "100.00",
    "hauteur_mm": "80.00",
    "nb_poses_laize": 3,
    "nb_poses_developpe": 2,
    "forme_speciale": False,
    "actif": True,
}

CLIENT_DEMO = {
    "nom": "Etiquettes Demo SAS",
    "contact": "Service achats",
    "email": "contact@example.invalid",
    "telephone": "00 00 00 00 00",
    "intervalle_dev_min_mm": "3.00",
    "actif": True,
}

OPTION_DEMO = {
    "code": "microperfo",
    "libelle": "Microperforation",
    "groupes_couleurs_requis": 0,
    "modules_requis": ["microperfo"],
    "coefficient_vitesse": "0.85",
    "coefficient_gache": "1.10",
    "temps_calage_ajoute_h": "0.25",
    "tarification": {"type": "forfait", "montant_eur": "45.00"},
    "silhouette_automatique": True,
    "actif": True,
}

# =============================================================================
#  SECTION 6 — parametres, calibration, baremes
#
#  Meme regle : ces champs sont tarifaires, ils ne s'ecrivent que dans CE
#  module. Les tests importent.
# =============================================================================

# Les NEUF champs que la calibration doit remplir (la marge est deja posee par
# l'installation, elle n'est pas ici).
PARAMETRES_COUTS_DEMO = {
    "cout_exploitation_machine_eur_h": "300.00",
    "cout_operateur_eur_h": "60.00",
    "marge_confort_roulage_mm": 20,
    "cliche_prix_couleur_eur": "40.00",
    "outil_base_eur": "250.00",
    "outil_par_trace_eur": "60.00",
    "surcout_forme_speciale_facteur": "1.50",
    "calage_forfait_eur": "200.00",
    "finitions_prix_m2_eur": "0.2000",
}

# Cas ROND, choisi pour se recontroler a la main :
#   240 000 / 10 = 24 000/an ; 24 000 / 1 600 = 15,00
#   12 000 / 1 600 = 7,50  ·  8 000 / 1 600 = 5,00  ->  taux = 27,50
CALIBRATION_RONDE = {
    "prix_achat_presse_eur": "240000.00",
    "duree_amortissement_ans": 10,
    "heures_productives_par_an": 1600,
    "energie_eur_an": "12000.00",
    "maintenance_eur_an": "8000.00",
}
CALIBRATION_RONDE_TAUX = "27.50"
CALIBRATION_RONDE_LIGNES = ("15.00", "7.50", "5.00")

# Cas NON ROND, choisi pour que les trois divisions tombent mal et que l'ecart
# entre « somme des lignes arrondies » et « total arrondi une fois » apparaisse :
#   187 500 / 7 = 26 785,714.../an ; / 1 700 = 15,756... -> 15,76
#   9 450 / 1 700 = 5,558... -> 5,56  ·  6 300 / 1 700 = 3,705... -> 3,71
#   somme des lignes  = 25,03      <- ce que rend l'API
#   total arrondi une fois = 25,02  <- ce qu'elle ne rend PAS, et c'est voulu
CALIBRATION_NON_RONDE = {
    "prix_achat_presse_eur": "187500.00",
    "duree_amortissement_ans": 7,
    "heures_productives_par_an": 1700,
    "energie_eur_an": "9450.00",
    "maintenance_eur_an": "6300.00",
}
CALIBRATION_NON_RONDE_TAUX = "25.03"
CALIBRATION_NON_RONDE_LIGNES = ("15.76", "5.56", "3.71")
CALIBRATION_NON_RONDE_TOTAL_ARRONDI_UNE_FOIS = "25.02"

# Un bareme calibre : des points, donc `neutre` a faux.
BAREME_CALIBRE = {
    "machines_ids": [],
    "donnees": {"points": [{"x": 10, "y": "1.05"}, {"x": 50, "y": "1.20"}]},
    "actif": True,
}
