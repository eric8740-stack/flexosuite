# -*- coding: utf-8 -*-
"""`GET` / `PUT /api/parametres/couts` — section 6 du contrat.

Le point le plus important de ce fichier n'est pas le `PUT` partiel : c'est
qu'**a l'installation, tout est vide sauf la marge**. L'application se livre a
ZERO TARIF, et ce test est le seul endroit ou cette promesse est verifiee du
cote de l'API.
"""
import pytest

from tests.fixtures.atelier_demo import PARAMETRES_COUTS_DEMO

CHEMIN = "/api/parametres/couts"

# Les onze cles du contrat : les dix champs, plus le booleen calcule.
CLES_ATTENDUES = frozenset(
    {
        "marge_standard_pct",
        "cout_exploitation_machine_eur_h",
        "cout_operateur_eur_h",
        "marge_confort_roulage_mm",
        "cliche_prix_couleur_eur",
        "outil_base_eur",
        "outil_par_trace_eur",
        "surcout_forme_speciale_facteur",
        "calage_forfait_eur",
        "finitions_prix_m2_eur",
        "calibration_faite",
    }
)

# Les neuf champs que la calibration doit remplir.
CHAMPS_A_REMPLIR = CLES_ATTENDUES - {"marge_standard_pct", "calibration_faite"}

# La valeur du contrat, ecrite telle qu'il l'ecrit. Ce n'est pas un tarif
# d'atelier mais une decision COMMERCIALE, confirmee a l'installation.
MARGE_LIVREE = "30.00"


def test_la_lecture_rend_exactement_les_onze_cles(client_installe):
    reponse = client_installe.get(CHEMIN)

    assert reponse.status_code == 200, reponse.text
    assert set(reponse.json()) == set(CLES_ATTENDUES)


def test_a_l_installation_tout_est_vide_sauf_la_marge(client_installe):
    """La promesse du projet, verifiee cote API : livrer les tarifs d'un autre
    atelier produirait des devis faux, et un devis faux se decouvre chez le
    client."""
    corps = client_installe.get(CHEMIN).json()

    assert corps["marge_standard_pct"] == MARGE_LIVREE
    assert all(corps[champ] is None for champ in CHAMPS_A_REMPLIR)
    assert corps["calibration_faite"] is False


def test_le_put_partiel_ne_touche_que_les_champs_envoyes(client_installe):
    """Le coeur du `PUT` partiel : un champ ABSENT n'est pas mis a `null`."""
    client_installe.put(CHEMIN, json=PARAMETRES_COUTS_DEMO)

    reponse = client_installe.put(
        CHEMIN, json={"cout_operateur_eur_h": PARAMETRES_COUTS_DEMO["cout_operateur_eur_h"]}
    )

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    for champ, valeur in PARAMETRES_COUTS_DEMO.items():
        assert corps[champ] == valeur, champ


def test_les_neuf_champs_remplis_font_basculer_calibration_faite(client_installe):
    avant = client_installe.get(CHEMIN).json()["calibration_faite"]

    apres = client_installe.put(CHEMIN, json=PARAMETRES_COUTS_DEMO).json()

    assert avant is False
    assert apres["calibration_faite"] is True


def test_un_seul_champ_manquant_laisse_calibration_faite_a_faux(client_installe):
    """Le contre-test : « les neuf » veut dire les neuf. Un test qui ne
    verifierait que le cas complet passerait aussi avec un booleen cable a
    vrai des le premier champ."""
    partiel = dict(PARAMETRES_COUTS_DEMO)
    del partiel["calage_forfait_eur"]

    corps = client_installe.put(CHEMIN, json=partiel).json()

    assert corps["calibration_faite"] is False


def test_le_contexte_dit_la_meme_chose_que_les_parametres(client_installe):
    """Le contrat rend `calibration_faite` aux deux endroits « pour ne pas
    avoir a le recalculer cote front ». Deux sources qui divergent seraient
    pires qu'une seule."""
    client_installe.put(CHEMIN, json=PARAMETRES_COUTS_DEMO)

    parametres = client_installe.get(CHEMIN).json()["calibration_faite"]
    contexte = client_installe.get("/api/contexte").json()["calibration_faite"]

    assert parametres is True
    assert contexte is True


def test_calibration_faite_envoye_est_IGNORE_et_non_refuse(client_installe):
    """Le contrat est explicite : « en ecriture, il est ignore ». Le refuser
    casserait le geste « je relis l'objet, je modifie un champ, je repose
    l'objet »."""
    reponse = client_installe.put(CHEMIN, json={"calibration_faite": True})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["calibration_faite"] is False


def test_la_marge_ne_peut_pas_etre_videe(client_installe):
    """Ne pas l'envoyer est permis — le `PUT` est partiel. L'envoyer vide, non :
    un devis calcule sans marge se vendrait au prix de revient."""
    reponse = client_installe.put(CHEMIN, json={"marge_standard_pct": None})

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"
    assert client_installe.get(CHEMIN).json()["marge_standard_pct"] == MARGE_LIVREE


def test_un_champ_inconnu_est_refuse(client_installe):
    reponse = client_installe.put(CHEMIN, json={"cout_du_cafe_eur": "1.20"})

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"


def test_les_montants_sortent_en_chaine(client_installe):
    corps = client_installe.put(CHEMIN, json=PARAMETRES_COUTS_DEMO).json()

    assert isinstance(corps["cout_operateur_eur_h"], str)
    assert isinstance(corps["finitions_prix_m2_eur"], str)
    # Quatre decimales sur un prix au m2, comme `matiere.prix_m2_eur`.
    assert corps["finitions_prix_m2_eur"] == PARAMETRES_COUTS_DEMO["finitions_prix_m2_eur"]
    # Et une dimension en millimetres reste un entier, pas une chaine.
    assert isinstance(corps["marge_confort_roulage_mm"], int)


@pytest.mark.parametrize("methode", ["get", "put"])
def test_sans_session_c_est_refuse(client_installe, methode):
    client_installe.cookies.clear()

    appel = getattr(client_installe, methode)
    reponse = appel(CHEMIN, json={}) if methode == "put" else appel(CHEMIN)

    assert reponse.status_code == 401, reponse.text
    assert reponse.json()["code"] == "session_absente"


def test_en_mode_demo_l_ecriture_est_refusee_mais_pas_la_lecture(
    client_installe, monkeypatch
):
    monkeypatch.setattr("app.dependances.DEMO_MODE", True)

    ecriture = client_installe.put(CHEMIN, json=PARAMETRES_COUTS_DEMO)
    lecture = client_installe.get(CHEMIN)

    assert ecriture.status_code == 403, ecriture.text
    assert ecriture.json()["code"] == "mode_demo_lecture_seule"
    assert lecture.status_code == 200, lecture.text
