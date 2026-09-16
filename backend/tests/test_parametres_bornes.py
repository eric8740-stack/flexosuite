# -*- coding: utf-8 -*-
"""Les bornes des parametres tarifaires — constat 1 de l'audit du 16/09/2026.

**Ce que ces tests protegent n'est pas une regle de saisie, c'est un devis.**

Avant correction, `PUT /api/parametres/couts` acceptait `-50.00` comme cout
operateur et rendait **200**, puis `calibration_faite` passait a **vrai**.
L'atelier croyait sa calibration faite ; le moteur du lot 2c aurait ete alimente
avec des couts negatifs. Un devis faux ne se decouvre pas au bureau : il se
decouvre **chez le client**.

Les bornes, arbitrees par Eric le 16/09/2026 :

- tous les couts et tarifs : `ge=0` ;
- `surcout_forme_speciale_facteur` : `ge=1` — c'est un FACTEUR multiplicatif, et
  un facteur sous 1 ferait qu'une forme speciale coute MOINS cher qu'une forme
  standard ;
- `marge_standard_pct` : `0 <= x <= 500` — garde anti-faute de frappe, pas une
  contrainte metier. La marge est sur COUT DE REVIENT et non un taux de marque :
  borner a 100 interdirait les coefficients au-dela de 2,0 que le petit tirage
  pratique reellement ;
- `marge_confort_roulage_mm` : `ge=0` (deja pose avant l'audit).
"""
import pytest

CHEMIN = "/api/parametres/couts"

# Un test par borne. Le libelle dit la borne, pas le champ : c'est la borne qui
# est la regle, et c'est elle qu'on lira dans un rapport d'echec.
COUTS_BORNES_A_ZERO = (
    "cout_exploitation_machine_eur_h",
    "cout_operateur_eur_h",
    "cliche_prix_couleur_eur",
    "outil_base_eur",
    "outil_par_trace_eur",
    "calage_forfait_eur",
    "finitions_prix_m2_eur",
)


@pytest.mark.parametrize("champ", COUTS_BORNES_A_ZERO)
def test_un_cout_NEGATIF_est_refuse(client_installe, champ):
    reponse = client_installe.put(CHEMIN, json={champ: "-1.00"})

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"
    assert champ in reponse.json()["detail"]


@pytest.mark.parametrize("champ", COUTS_BORNES_A_ZERO)
def test_un_cout_a_ZERO_reste_accepte(client_installe, champ):
    """Zero n'est pas une aberration : un atelier peut ne rien facturer d'un poste."""
    reponse = client_installe.put(CHEMIN, json={champ: "0.00"})

    assert reponse.status_code == 200, reponse.text


def test_le_facteur_de_surcout_SOUS_UN_est_refuse(client_installe):
    """Un facteur sous 1 rendrait une forme speciale MOINS chere qu'une standard."""
    reponse = client_installe.put(
        CHEMIN, json={"surcout_forme_speciale_facteur": "0.50"}
    )

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"
    assert "surcout_forme_speciale_facteur" in reponse.json()["detail"]


def test_le_facteur_de_surcout_a_UN_reste_accepte(client_installe):
    """1,00 = pas de surcout. C'est la valeur neutre, elle doit passer."""
    reponse = client_installe.put(
        CHEMIN, json={"surcout_forme_speciale_facteur": "1.00"}
    )

    assert reponse.status_code == 200, reponse.text


def test_une_marge_NEGATIVE_est_refusee(client_installe):
    reponse = client_installe.put(CHEMIN, json={"marge_standard_pct": "-1.00"})

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"
    assert "marge_standard_pct" in reponse.json()["detail"]


def test_une_marge_AU_DELA_DE_500_est_refusee(client_installe):
    """La faute de frappe visee : 3000 au lieu de 30."""
    reponse = client_installe.put(CHEMIN, json={"marge_standard_pct": "3000.00"})

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"
    assert "marge_standard_pct" in reponse.json()["detail"]


def test_une_marge_de_500_reste_acceptee(client_installe):
    """La borne est INCLUSE : 500 passe, 500,01 non. Un test dirait le contraire
    sans qu'on le voie si on ne testait que la valeur refusee."""
    reponse = client_installe.put(CHEMIN, json={"marge_standard_pct": "500.00"})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["marge_standard_pct"] == "500.00"


def test_une_marge_de_150_pct_reste_acceptee(client_installe):
    """C'est le cas qui a fait REFUSER la borne a 100 proposee par l'audit.

    150 % sur cout de revient = coefficient 2,5. Le petit tirage le pratique.
    Ce test est la pour qu'un futur resserrement de la borne rougisse.
    """
    reponse = client_installe.put(CHEMIN, json={"marge_standard_pct": "150.00"})

    assert reponse.status_code == 200, reponse.text


def test_une_marge_de_confort_NEGATIVE_est_refusee(client_installe):
    reponse = client_installe.put(CHEMIN, json={"marge_confort_roulage_mm": -1})

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"


def test_la_calibration_ne_se_declare_PAS_faite_avec_des_valeurs_hors_borne(
    client_installe,
):
    """Le vrai degat du constat 1, en un test.

    Avant correction : tout passait en 200 et `calibration_faite` devenait vrai.
    L'atelier croyait sa calibration faite avec des couts negatifs.
    """
    absurdes = {champ: "-50.00" for champ in COUTS_BORNES_A_ZERO}
    absurdes["surcout_forme_speciale_facteur"] = "-2.00"

    reponse = client_installe.put(CHEMIN, json=absurdes)
    assert reponse.status_code == 422, reponse.text

    # Et rien n'a ete range au passage : la lecture doit etre inchangee.
    apres = client_installe.get(CHEMIN).json()
    assert apres["calibration_faite"] is False
    assert apres["cout_operateur_eur_h"] is None
