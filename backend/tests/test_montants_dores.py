# -*- coding: utf-8 -*-
"""Les montants dores — le cahier de recette du moteur.

Ces tests sont ecrits AVANT l'implementation, et ils sont la raison d'etre du
lot 1. Ils viennent de `docs/SPEC-METIER.md`.

⚠️ Regle absolue : **un montant dore ne se retouche jamais pour faire tomber un
calcul.** Un ecart se signale a Eric ; il ne se corrige pas en changeant
l'attendu. Une re-baseline demande sa validation explicite.
"""
from decimal import Decimal

import pytest

from app.moteur.couts import chiffrer, chiffrer_lots
from app.moteur.types import EntreeChiffrage
from tests.fixtures import atelier_demo as demo


# =============================================================================
#  Cas A — atelier rond, mono-lot : 1 777,00 EUR HT
# =============================================================================
def _entree_a() -> EntreeChiffrage:
    return EntreeChiffrage(
        matiere=demo.MATIERE_A,
        machine=demo.MACHINE_A,
        laize_utile_mm=Decimal("220"),
        laize_papier_mm=Decimal("210"),
        ml_total=3000,
        couleurs_par_type={"quadri": 4, "pantone": 1},
        tarifs_encre=demo.ENCRES_A,
        forfaits_sous_traitance=[demo.FORFAIT_ST_A],
    )


def test_cas_a_poste_par_poste():
    """Chaque poste est verifie separement : un total juste par compensation de
    deux erreurs resterait invisible."""
    r = chiffrer(_entree_a(), demo.PARAMETRES_A)
    attendus = {
        1: Decimal("315.00"),   # 630 m2 -> 63 kg x 5,00
        2: Decimal("138.60"),   # quadri 105,60 + pantone 33,00
        3: Decimal("200.00"),   # 5 couleurs x 40,00, outil existant
        4: Decimal("200.00"),   # forfait x 1 calage
        5: Decimal("180.00"),   # 0,6 h x 300,00
        6: Decimal("232.00"),   # 132,00 + forfait 100,00
        7: Decimal("156.00"),   # 2,6 h x 60,00
    }
    obtenus = {p.numero: p.montant_eur for p in r.postes}
    assert obtenus == attendus


def test_cas_a_total():
    r = chiffrer(_entree_a(), demo.PARAMETRES_A)
    assert r.cout_revient_eur == Decimal("1421.60")
    assert r.prix_vente_ht_eur == Decimal("1777.00")


def test_cas_a_le_coefficient_est_expose():
    """La marge est une marge SUR COUT DE REVIENT, pas un taux de marque. Le
    moteur expose le coefficient pour que l'interface ne laisse pas
    l'imprimeur le deduire — a 30 %, un taux de marque donnerait 1,4286."""
    r = chiffrer(_entree_a(), demo.PARAMETRES_A)
    assert r.coefficient == Decimal("1.25")
    assert r.cout_revient_eur * r.coefficient == Decimal("1777.0000")


# =============================================================================
#  Cas B — atelier non rond : 1 587,66 EUR HT. Celui qui exerce les arrondis.
# =============================================================================
def _entree_b() -> EntreeChiffrage:
    return EntreeChiffrage(
        matiere=demo.MATIERE_B,
        machine=demo.MACHINE_B,
        laize_utile_mm=Decimal("213"),
        laize_papier_mm=Decimal("197"),
        ml_total=2750,
        couleurs_par_type={"quadri": 3, "pantone": 2},
        tarifs_encre=demo.ENCRES_B,
        forfaits_sous_traitance=[demo.FORFAIT_ST_B],
    )


def test_cas_b_poste_par_poste():
    r = chiffrer(_entree_b(), demo.PARAMETRES_B)
    attendus = {
        1: Decimal("231.60"),
        2: Decimal("129.40"),
        3: Decimal("189.00"),
        4: Decimal("193.60"),
        5: Decimal("167.12"),
        6: Decimal("197.18"),
        7: Decimal("137.32"),
    }
    obtenus = {p.numero: p.montant_eur for p in r.postes}
    assert obtenus == attendus


def test_cas_b_l_arrondi_final_mord():
    """1 245,22 x 1,275 = 1 587,6555. Un moteur qui arrondirait ailleurs, ou
    dans un autre ordre, sortirait un centime a cote."""
    r = chiffrer(_entree_b(), demo.PARAMETRES_B)
    assert r.cout_revient_eur == Decimal("1245.22")
    assert r.prix_vente_ht_eur == Decimal("1587.66")


def test_cas_b_les_sous_totaux_d_encre_se_somment_bruts():
    """Piege verifie : le poste Encres somme ses sous-totaux BRUTS et n'arrondit
    qu'une fois. Arrondir chaque part d'abord donnerait le meme resultat ici —
    d'ou l'interet de le verifier explicitement plutot que de s'en remettre au
    total."""
    r = chiffrer(_entree_b(), demo.PARAMETRES_B)
    p2 = next(p for p in r.postes if p.numero == 2)
    assert p2.details["conso_kg_quadri"] == Decimal("3.7780875")
    assert p2.details["conso_kg_pantone"] == Decimal("2.518725")
    assert p2.montant_eur == Decimal("129.40")


# =============================================================================
#  Cas multi-lots — et la regle du calage
# =============================================================================
def _entree_multilots(changement: bool = False) -> EntreeChiffrage:
    """Fixture M1 : 3 poses en laize x 2 en developpe, 10 000 etiquettes,
    AUCUNE couleur (le poste Encres vaut 0, le cas reste deterministe)."""
    return EntreeChiffrage(
        matiere=demo.MATIERE_A,
        machine=demo.MACHINE_A,
        laize_utile_mm=Decimal("320"),
        laize_papier_mm=Decimal("320"),
        ml_total=501,
        couleurs_par_type={},
        tarifs_encre=demo.ENCRES_A,
        forfaits_sous_traitance=[],
        changement_outil_cliche=changement,
    )


def test_m1_un_seul_lot():
    r = chiffrer_lots([_entree_multilots()], demo.PARAMETRES_A)
    assert r.cout_revient_eur == Decimal("468.29")
    assert r.prix_vente_ht_eur == Decimal("585.36")


def test_m1_decomposition():
    """Le metrage alimente quatre postes : s'il derive, tout derive."""
    r = chiffrer_lots([_entree_multilots()], demo.PARAMETRES_A)
    attendus = {
        1: Decimal("80.16"), 2: Decimal("0.00"), 3: Decimal("0.00"),
        4: Decimal("200.00"), 5: Decimal("30.06"), 6: Decimal("32.06"),
        7: Decimal("126.01"),
    }
    obtenus = {p.numero: p.montant_eur for p in r.lots[0].postes}
    assert obtenus == attendus


def test_m2_deux_lots_meme_montage_un_seul_calage():
    r = chiffrer_lots([_entree_multilots(), _entree_multilots()], demo.PARAMETRES_A)
    assert r.prix_vente_ht_eur == Decimal("920.72")
    assert r.nb_calages == 1


def test_m3_deux_lots_avec_changement_deux_calages():
    r = chiffrer_lots(
        [_entree_multilots(), _entree_multilots(changement=True)], demo.PARAMETRES_A
    )
    assert r.prix_vente_ht_eur == Decimal("1170.72")
    assert r.nb_calages == 2


def test_le_premier_lot_ne_porte_jamais_le_drapeau():
    """Le calage du premier lot est inclus : son drapeau est ignore, sans quoi
    une saisie fautive facturerait deux calages pour un seul montage."""
    r = chiffrer_lots([_entree_multilots(changement=True)], demo.PARAMETRES_A)
    assert r.nb_calages == 1
    assert r.prix_vente_ht_eur == Decimal("585.36")


# =============================================================================
#  Les trois invariants — vrais sans recalculer un seul poste
# =============================================================================
def test_invariant_le_delta_vaut_exactement_un_calage():
    m2 = chiffrer_lots([_entree_multilots(), _entree_multilots()], demo.PARAMETRES_A)
    m3 = chiffrer_lots(
        [_entree_multilots(), _entree_multilots(changement=True)], demo.PARAMETRES_A
    )
    calage_majore = demo.PARAMETRES_A.calage_forfait_eur * (
        1 + demo.PARAMETRES_A.marge_standard_pct / 100
    )
    assert m3.prix_vente_ht_eur - m2.prix_vente_ht_eur == Decimal("250.00")
    assert calage_majore == Decimal("250.0000")


def test_invariant_le_second_lot_vaut_le_premier_moins_son_calage():
    m1 = chiffrer_lots([_entree_multilots()], demo.PARAMETRES_A)
    m2 = chiffrer_lots([_entree_multilots(), _entree_multilots()], demo.PARAMETRES_A)
    assert m2.prix_vente_ht_eur == m1.prix_vente_ht_eur + Decimal("335.36")
    assert m2.lots[1].prix_vente_ht_eur == Decimal("335.36")


def test_invariant_deux_montages_distincts_valent_deux_fois_le_lot_seul():
    m1 = chiffrer_lots([_entree_multilots()], demo.PARAMETRES_A)
    m3 = chiffrer_lots(
        [_entree_multilots(), _entree_multilots(changement=True)], demo.PARAMETRES_A
    )
    assert m3.prix_vente_ht_eur == m1.prix_vente_ht_eur * 2


@pytest.mark.parametrize("nb_lots", [1, 2])
def test_invariant_le_detail_somme_au_total(nb_lots):
    """Un total juste avec un detail qui ne somme pas est un devis que le
    deviseur ne peut pas defendre."""
    r = chiffrer_lots([_entree_multilots() for _ in range(nb_lots)], demo.PARAMETRES_A)
    assert sum((l.prix_vente_ht_eur for l in r.lots), Decimal(0)) == r.prix_vente_ht_eur


def test_la_trace_du_calage_mutualise_est_exposee():
    """C'est elle qui explique au client pourquoi son second lot coute moins
    cher — un argument commercial, pas une ligne technique."""
    r = chiffrer_lots([_entree_multilots(), _entree_multilots()], demo.PARAMETRES_A)
    assert r.lots[0].calage_mutualise_eur == Decimal("0.00")
    assert r.lots[1].calage_mutualise_eur == Decimal("200.00")
