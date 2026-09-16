# -*- coding: utf-8 -*-
"""`neutre` — constat 3 de l'audit du 16/09/2026.

`neutre` commande un affichage qui engage un prix : tant qu'il vaut vrai, le
front doit **dire** que les scores sont indicatifs. Un score indicatif presente
comme regle fait prendre une decision de prix sur un chiffre qui ne veut rien
dire.

Avant correction, le calcul etait « une valeur quelconque de `donnees` est-elle
vraie ? ». Mesure sur dix formes : **quatre ecarts**, et l'erreur allait **dans
les deux sens**. Ce fichier fige les deux sens, parce qu'un seul des deux se
serait fait oublier.
"""
import pytest

from app.models.baremes import Bareme


def _bareme(donnees):
    return Bareme(
        type="echenillage", libelle="Echenillage", machines_ids=[],
        donnees=donnees, actif=True,
    )


# --- Ce qui est NEUTRE : aucun point pose ------------------------------------
NEUTRES = [
    pytest.param({"points": []}, id="forme_livree"),
    pytest.param({}, id="dictionnaire_vide"),
    pytest.param({"points": [], "version": 1}, id="metadonnee_SANS_point"),
    pytest.param({"points": [], "commentaire": "a refaire"}, id="commentaire_seul"),
    pytest.param({"version": 3}, id="metadonnee_sans_clef_points"),
    # Une valeur *falsy* hors `points` ne calibre rien non plus — mais elle ne
    # doit plus etre ce qui DECIDE : c'est l'absence de points qui decide.
    pytest.param({"coefficient": 0}, id="valeur_falsy_hors_points"),
]


@pytest.mark.parametrize("donnees", NEUTRES)
def test_un_bareme_SANS_POINT_est_neutre(donnees):
    assert _bareme(donnees).neutre is True


# --- Ce qui est CALIBRE : au moins un point ----------------------------------
CALIBRES = [
    pytest.param({"points": [{"x": 1, "y": 2}]}, id="un_point"),
    pytest.param({"points": [{"x": 1}], "version": 2}, id="un_point_ET_metadonnee"),
    pytest.param({"points": [{}]}, id="un_point_vide_reste_un_point"),
    pytest.param({"points": [0]}, id="un_point_a_zero_reste_un_point"),
]


@pytest.mark.parametrize("donnees", CALIBRES)
def test_un_bareme_AVEC_POINTS_n_est_pas_neutre(donnees):
    assert _bareme(donnees).neutre is False


# --- Les regressions exactes que l'audit a mesurees --------------------------
def test_une_METADONNEE_seule_ne_fait_plus_croire_a_une_calibration():
    """Le sens le plus grave, et celui que je n'avais pas vu seul.

    AVANT : `{"points": [], "version": 1}` rendait `neutre=False`. Le front
    cessait d'avertir que les scores etaient indicatifs — alors qu'aucun point
    n'etait pose.
    """
    assert _bareme({"points": [], "version": 1}).neutre is True


def test_une_valeur_FALSY_ne_decide_plus_de_la_neutralite():
    """AVANT : `{"coefficient": 0}` et `{"actif_courbe": False}` rendaient
    `neutre=True` en passant par le test de veracite. Ils le rendent toujours,
    mais pour la bonne raison — aucun point n'est pose — et non parce que zero
    est faux."""
    assert _bareme({"coefficient": 0, "points": [{"x": 1}]}).neutre is False


def test_des_donnees_NON_DICT_ne_font_pas_tomber_le_calcul():
    """Pydantic impose `donnees: dict` a l'entree de l'API, donc ce cas ne
    devrait pas arriver. La garde est la pour une base ecrite autrement — une
    migration, un script de reprise — ou un 500 sur un simple `GET` serait une
    punition disproportionnee."""
    assert _bareme(["pas", "un", "dict"]).neutre is True
    assert _bareme(None).neutre is True
