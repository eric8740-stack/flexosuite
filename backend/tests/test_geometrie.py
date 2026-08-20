# -*- coding: utf-8 -*-
"""La chaine de pose et les sens d'enroulement.

Les valeurs viennent du § 5 ter et du § 5 quater de docs/SPEC-METIER.md, et du
cas de reference multi-lots : etiquette 100 x 80, 3 poses en laize, laize utile
320, cylindre de developpe 300, 10 000 etiquettes.
"""
from decimal import Decimal

import pytest

from app.moteur import geometrie as g
from app.moteur.sens import paire_indiscernable, sens


# --- Chaine de laize, sur le cas de reference --------------------------------
def test_l_intervalle_en_laize_est_plafonne():
    """L'espace disponible autoriserait 10 mm ; le plafond metier ramene a 5."""
    assert g.intervalle_en_laize(Decimal("320"), Decimal("100"), 3) == Decimal("5")


def test_la_plaque_compte_les_intervalles_INTERNES():
    """3 x 100 + 2 x 5 = 310. Les 2 x 5 ne sont PAS les bords."""
    assert g.laize_plaque(Decimal("100"), 3, Decimal("5")) == Decimal("310")


def test_le_plafond_de_laize_utile_mord():
    """Le brut arrondi au palier depasse la laize utile : la presse rogne."""
    papier = g.laize_papier(
        laize_plaque_mm=Decimal("310"),
        bord_lateral_mm=Decimal("8"),
        palier_fournisseur_mm=10,
        laize_utile_mm=Decimal("320"),
    )
    assert papier == Decimal("320")


def test_sans_plafond_le_palier_superieur_s_applique():
    """310 + 2 x 8 = 326, arrondi au palier de 10 -> 330."""
    papier = g.laize_papier(Decimal("310"), Decimal("8"), 10)
    assert papier == Decimal("330")


def test_le_plancher_de_roulabilite_s_applique_apres_le_plafond():
    papier = g.laize_papier(
        Decimal("100"), Decimal("2"), 10,
        laize_utile_mm=Decimal("110"), laize_mini_roulable_mm=Decimal("150"),
    )
    assert papier == Decimal("150")


def test_la_plaque_est_centree():
    assert g.chute_par_cote(Decimal("320"), Decimal("310")) == Decimal("5")


# --- Poses en developpe -------------------------------------------------------
def test_les_poses_en_developpe_redistribuent_l_intervalle():
    """300 / (80 + 3) -> 3 poses ; l'intervalle reel remonte a 20 mm."""
    nb, intervalle = g.poses_en_developpe(Decimal("300"), Decimal("80"), Decimal("3"))
    assert nb == 3
    assert intervalle == Decimal("20")


def test_on_retire_une_pose_plutot_que_de_passer_sous_le_minimum():
    """Le plancher donnerait 3 poses a 0 mm d'intervalle : inacceptable, le
    squelette casserait. On descend a 2 poses, intervalle 20 mm."""
    nb, intervalle = g.poses_en_developpe(Decimal("240"), Decimal("80"), Decimal("5"))
    assert nb == 2
    assert intervalle == Decimal("40")


def test_aucune_pose_possible_renvoie_rien():
    assert g.poses_en_developpe(Decimal("50"), Decimal("80"), Decimal("3")) is None


# --- Metrage ------------------------------------------------------------------
def test_le_metrage_monte_deux_fois():
    """10 000 / 6 -> 1 667 tours (on finit le tour entame), soit 500,10 m,
    arrondi au metre superieur : 501. C'est la valeur du cas de reference."""
    assert g.metrage(10_000, 3, 2, Decimal("300")) == 501


def test_un_multiple_exact_ne_gonfle_pas_le_nombre_de_tours():
    """9 996 / 6 = 1 666 tours pile -> 499,80 m -> 500 m (seule la seconde
    montee joue)."""
    assert g.metrage(9_996, 3, 2, Decimal("300")) == 500


def test_une_etiquette_de_plus_coute_un_tour_entier():
    """9 996 est le multiple exact de 6 poses : une seule etiquette de plus
    entame un tour, et le tour entame se finit."""
    assert g.metrage(9_996, 3, 2, Decimal("300")) == 500   # 1 666 tours pile
    assert g.metrage(9_997, 3, 2, Decimal("300")) == 501   # 1 667 tours
    assert g.metrage(10_002, 3, 2, Decimal("300")) == 501  # 1 667 tours pile
    assert g.metrage(10_003, 3, 2, Decimal("300")) == 501  # 1 668 -> 500,4 -> 501


def test_le_rendement_se_calcule_sur_la_surface_consommee():
    surface = g.surface_consommee_m2(501, Decimal("320"))
    assert surface == Decimal("160.32")
    r = g.rendement_pct(10_000, Decimal("100"), Decimal("80"), surface)
    assert r.quantize(Decimal("0.01")) == Decimal("49.90")


# --- Sens d'enroulement -------------------------------------------------------
@pytest.mark.parametrize("numero", [1, 2, 3, 4])
def test_les_paires_partagent_les_memes_rotations(numero):
    """C'est LE piege : exterieur et interieur sont indiscernables sur la
    planche et sur la bobine deroulee."""
    a, b = sens(numero), sens(numero + 4)
    assert a.rotation_vue_planche == b.rotation_vue_planche
    assert a.rotation_vue_bobine == b.rotation_vue_bobine
    assert a.face != b.face
    assert paire_indiscernable(numero) == numero + 4


def test_les_rotations_sont_celles_de_la_convention():
    assert sens(1).rotation_vue_planche == 90
    assert sens(1).rotation_vue_bobine == 0
    assert sens(3).rotation_vue_planche == 0
    assert sens(3).rotation_vue_bobine == 270


@pytest.mark.parametrize("mauvais", [0, 9, -1])
def test_un_sens_hors_bornes_leve_une_erreur(mauvais):
    """Pas de valeur par defaut : un sens invente oriente un cliche au hasard,
    et le tirage part a la benne."""
    with pytest.raises(ValueError):
        sens(mauvais)
