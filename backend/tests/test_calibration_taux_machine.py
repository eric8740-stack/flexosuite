# -*- coding: utf-8 -*-
"""`POST /api/calibration/taux-machine` — un calcul, pas une ecriture.

Deux proprietes sont verifiees ici, et la seconde est la plus facile a perdre :

1. le calcul **ne s'enregistre pas tout seul** — c'est un `PUT` sur les
   parametres qui decide ;
2. **les lignes du detail s'additionnent pour donner le taux.** Le contrat rend
   le detail « parce qu'un chiffre qu'on ne sait pas justifier ne sera pas
   adopte ». Un imprimeur qui additionne les trois lignes affichees et ne
   retombe pas sur le taux affiche cesse de croire l'outil, pas son addition.
"""
from decimal import Decimal

from tests.fixtures.atelier_demo import (
    CALIBRATION_NON_RONDE,
    CALIBRATION_NON_RONDE_LIGNES,
    CALIBRATION_NON_RONDE_TAUX,
    CALIBRATION_NON_RONDE_TOTAL_ARRONDI_UNE_FOIS,
    CALIBRATION_RONDE,
    CALIBRATION_RONDE_LIGNES,
    CALIBRATION_RONDE_TAUX,
)

CHEMIN = "/api/calibration/taux-machine"
PARAMETRES = "/api/parametres/couts"


def test_le_cas_rond_donne_le_taux_du_contrat(client_installe):
    reponse = client_installe.post(CHEMIN, json=CALIBRATION_RONDE)

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert set(corps) == {"taux_eur_h", "detail"}
    assert corps["taux_eur_h"] == CALIBRATION_RONDE_TAUX


def test_le_detail_nomme_les_trois_postes_dans_l_ordre(client_installe):
    corps = client_installe.post(CHEMIN, json=CALIBRATION_RONDE).json()

    assert [ligne["libelle"] for ligne in corps["detail"]] == [
        "Amortissement",
        "Energie",
        "Maintenance",
    ]
    assert [ligne["montant_eur_h"] for ligne in corps["detail"]] == list(
        CALIBRATION_RONDE_LIGNES
    )


def test_les_lignes_s_additionnent_pour_donner_le_taux(client_installe):
    """Vrai sur le cas rond — ou c'est facile — comme sur le cas non rond, ou
    les trois divisions tombent mal."""
    for entree in (CALIBRATION_RONDE, CALIBRATION_NON_RONDE):
        corps = client_installe.post(CHEMIN, json=entree).json()

        somme = sum(Decimal(ligne["montant_eur_h"]) for ligne in corps["detail"])
        assert somme == Decimal(corps["taux_eur_h"]), entree


def test_le_cas_non_rond_rend_la_somme_des_lignes_pas_le_total_arrondi(
    client_installe,
):
    """Le centime d'ecart est VOULU, et c'est ce test qui l'enregistre.

    Si un jour quelqu'un « corrige » le calcul en arrondissant le total une
    seule fois, ce test tombe — et il faudra relire l'en-tete de
    `app/services/calibration.py` avant de le changer."""
    corps = client_installe.post(CHEMIN, json=CALIBRATION_NON_RONDE).json()

    assert corps["taux_eur_h"] == CALIBRATION_NON_RONDE_TAUX
    assert corps["taux_eur_h"] != CALIBRATION_NON_RONDE_TOTAL_ARRONDI_UNE_FOIS
    assert [ligne["montant_eur_h"] for ligne in corps["detail"]] == list(
        CALIBRATION_NON_RONDE_LIGNES
    )


def test_le_calcul_n_enregistre_rien(client_installe):
    """« Le calcul ne s'enregistre pas tout seul : il propose. »"""
    avant = client_installe.get(PARAMETRES).json()

    client_installe.post(CHEMIN, json=CALIBRATION_RONDE)

    assert client_installe.get(PARAMETRES).json() == avant


def test_les_montants_sortent_en_chaine(client_installe):
    corps = client_installe.post(CHEMIN, json=CALIBRATION_RONDE).json()

    assert isinstance(corps["taux_eur_h"], str)
    assert all(isinstance(ligne["montant_eur_h"], str) for ligne in corps["detail"])


def test_une_duree_nulle_est_refusee_et_ne_provoque_pas_de_division_par_zero(
    client_installe,
):
    entree = dict(CALIBRATION_RONDE)
    entree["duree_amortissement_ans"] = 0

    reponse = client_installe.post(CHEMIN, json=entree)

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"


def test_des_heures_productives_nulles_sont_refusees(client_installe):
    entree = dict(CALIBRATION_RONDE)
    entree["heures_productives_par_an"] = 0

    reponse = client_installe.post(CHEMIN, json=entree)

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"


def test_un_champ_inconnu_est_refuse(client_installe):
    entree = dict(CALIBRATION_RONDE)
    entree["nombre_d_operateurs"] = 2

    reponse = client_installe.post(CHEMIN, json=entree)

    assert reponse.status_code == 422, reponse.text


def test_sans_session_c_est_refuse(client_installe):
    client_installe.cookies.clear()

    reponse = client_installe.post(CHEMIN, json=CALIBRATION_RONDE)

    assert reponse.status_code == 401, reponse.text
    assert reponse.json()["code"] == "session_absente"


def test_en_mode_demo_le_calcul_reste_accessible(client_installe, monkeypatch):
    """⚠️ **Decision assumee, pas un oubli.** C'est un `POST`, mais il n'ecrit
    rien : le refuser retirerait a la demonstration publique l'ecran qui montre
    le mieux ce que fait l'application, sans rien proteger.

    Ce test est la sentinelle de ce choix. Le jour ou cet endpoint ecrira quoi
    que ce soit, il faut remettre `interdire_ecriture_demo` sur son routeur — et
    ce test tombera, ce qui est exactement le rappel voulu."""
    monkeypatch.setattr("app.dependances.DEMO_MODE", True)

    reponse = client_installe.post(CHEMIN, json=CALIBRATION_RONDE)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["taux_eur_h"] == CALIBRATION_RONDE_TAUX
