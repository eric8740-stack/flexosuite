# -*- coding: utf-8 -*-
"""La forme rendue est-elle CELLE DU CONTRAT ?

Ce fichier ne verifie pas que le code fait ce qu'il fait : il verifie que ce
qu'il rend correspond a `docs/CONTRAT-API.md`, section 5. Les cles attendues
sont ecrites a la main dans `tests/aide_referentiels.py`, a partir du document —
pas deduites des schemas, sinon un champ renomme des deux cotes passerait
inapercu et le front tomberait seul.

Le test central est un **aller-retour a l'identique** : ce qui ressort est
exactement ce qui est entre. Il attrape d'un coup les trois facons de casser le
contrat sans s'en apercevoir — un decimal rendu en flottant (`320.0` au lieu de
`"320.00"`), un `null` transforme en valeur par defaut, une liste aplatie.
"""
import pytest

from tests.aide_referentiels import CYLINDRES, MATIERES, OPTIONS, TOUTES, corps_complet


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_la_creation_rend_exactement_les_cles_du_contrat(client_installe, cas):
    corps = corps_complet(client_installe, cas)

    reponse = client_installe.post(cas.chemin, json=corps)

    assert reponse.status_code == 201, reponse.text
    assert set(reponse.json()) == set(cas.cles_attendues)


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_la_creation_rend_a_l_identique_ce_qui_a_ete_envoye(client_installe, cas):
    corps = corps_complet(client_installe, cas)

    recu = client_installe.post(cas.chemin, json=corps).json()

    assert {champ: recu[champ] for champ in corps} == corps


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_la_relecture_rend_la_meme_chose_que_la_creation(client_installe, cas):
    """Rendre le bon corps a la creation ne prouve rien : l'API peut renvoyer
    l'echo de ce qu'on lui a donne sans l'avoir range correctement. C'est la
    RELECTURE qui traverse reellement la base."""
    corps = corps_complet(client_installe, cas)
    cree = client_installe.post(cas.chemin, json=corps).json()

    reponse = client_installe.get(f"{cas.chemin}/{cree['id']}")

    assert reponse.status_code == 200, reponse.text
    assert reponse.json() == cree


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_les_elements_de_la_liste_ont_la_meme_forme_que_l_unitaire(
    client_installe, cas
):
    corps = corps_complet(client_installe, cas)
    cree = client_installe.post(cas.chemin, json=corps).json()

    reponse = client_installe.get(cas.chemin)

    assert reponse.status_code == 200, reponse.text
    corps_liste = reponse.json()
    assert set(corps_liste) == {"elements", "total"}
    assert corps_liste["elements"] == [cree]


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_un_champ_inconnu_est_refuse(client_installe, cas):
    """Un champ que le contrat ne porte pas est une faute de frappe ou un
    contrat mal lu. L'ignorer en silence laisserait croire qu'il a ete
    enregistre."""
    corps = dict(corps_complet(client_installe, cas))
    corps["champ_qui_n_existe_pas"] = 1

    reponse = client_installe.post(cas.chemin, json=corps)

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"


def test_le_decimal_sort_en_chaine_pas_en_flottant(client_installe):
    """Le contrat : « serialises en chaine, jamais en nombre flottant »."""
    corps = corps_complet(client_installe, MATIERES)

    recu = client_installe.post(MATIERES.chemin, json=corps).json()

    assert isinstance(recu["prix_m2_eur"], str)
    assert isinstance(recu["grammage_g_m2"], str)
    # Quatre decimales conservees : au m2, la troisieme et la quatrieme pesent
    # sur un tirage de plusieurs milliers de metres.
    assert recu["prix_m2_eur"].split(".")[1] == corps["prix_m2_eur"].split(".")[1]


def test_le_nombre_de_dents_accepte_le_nul_et_le_rend_nul(client_installe):
    """v1.2 : `nb_dents` est un repere de catalogue FACULTATIF. C'est
    `developpe_mm` qui fait foi pour la geometrie."""
    corps = corps_complet(client_installe, CYLINDRES)
    assert corps["nb_dents"] is None

    recu = client_installe.post(CYLINDRES.chemin, json=corps).json()

    assert recu["nb_dents"] is None
    assert recu["developpe_mm"] == corps["developpe_mm"]


def test_l_epaisseur_reelle_est_obligatoire(client_installe):
    """Pas de defaut acceptable : le diametre de bobine se calcule dessus, et
    une epaisseur inventee donne un metrage par bobine faux."""
    corps = dict(corps_complet(client_installe, MATIERES))
    del corps["epaisseur_reelle_micron"]

    reponse = client_installe.post(MATIERES.chemin, json=corps)

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"
    assert "epaisseur_reelle_micron" in reponse.json()["detail"]


def test_la_tarification_refuse_un_type_hors_contrat(client_installe):
    """`forfait`, `m2` ou `mille` — et rien d'autre."""
    corps = dict(corps_complet(client_installe, OPTIONS))
    corps["tarification"] = dict(corps["tarification"])
    corps["tarification"]["type"] = "au_kilo"

    reponse = client_installe.post(OPTIONS.chemin, json=corps)

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"


def test_la_tarification_traverse_la_base_sans_se_deformer(client_installe):
    """Structure imbriquee rangee en JSON texte : c'est le seul endroit du lot
    ou une valeur pourrait revenir avec une autre forme que celle envoyee."""
    corps = corps_complet(client_installe, OPTIONS)
    cree = client_installe.post(OPTIONS.chemin, json=corps).json()

    relu = client_installe.get(f"{OPTIONS.chemin}/{cree['id']}").json()

    assert relu["tarification"] == corps["tarification"]
    assert relu["modules_requis"] == corps["modules_requis"]
