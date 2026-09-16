# -*- coding: utf-8 -*-
"""`GET /api/baremes` · `PUT /api/baremes/{type}` — section 6 du contrat.

Les quatre types sont fixes, livres **en mode neutre**, et crees a la volee au
premier acces : une installation faite avant ce lot doit se retrouver avec ses
quatre baremes sans intervention.
"""
from tests.aide_referentiels import creer_machine
from tests.fixtures.atelier_demo import BAREME_CALIBRE

CHEMIN = "/api/baremes"

TYPES_ATTENDUS = [
    "echenillage",
    "effet_banane",
    "confort_roulage",
    "compensation_laize_dev",
]

CLES_ATTENDUES = frozenset(
    {"type", "libelle", "neutre", "machines_ids", "donnees", "actif"}
)

DONNEES_VIDES: dict = {"points": []}


def test_les_quatre_baremes_existent_des_le_premier_acces(client_installe):
    """Aucune migration ne les insere, aucun assistant ne les pose : ils
    apparaissent en arrivant. Une ligne manquante ne peut pas casser l'ecran."""
    reponse = client_installe.get(CHEMIN)

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["total"] == 4
    assert [b["type"] for b in corps["elements"]] == TYPES_ATTENDUS


def test_la_liste_rend_l_enveloppe_et_pas_un_tableau_nu(client_installe):
    corps = client_installe.get(CHEMIN).json()

    assert set(corps) == {"elements", "total"}
    assert set(corps["elements"][0]) == set(CLES_ATTENDUES)


def test_l_appel_repete_ne_cree_pas_de_doublon(client_installe):
    """La creation a la volee doit etre IDEMPOTENTE : sinon chaque
    rafraichissement de l'ecran ajouterait quatre lignes."""
    client_installe.get(CHEMIN)
    client_installe.get(CHEMIN)

    assert client_installe.get(CHEMIN).json()["total"] == 4


def test_ils_sont_livres_neutres(client_installe):
    """Coefficients a 1,0, aucune configuration favorisee : livrer les courbes
    reglees sur le parc d'un autre atelier produirait des scores faux."""
    elements = client_installe.get(CHEMIN).json()["elements"]

    assert all(b["neutre"] is True for b in elements)
    assert all(b["donnees"] == DONNEES_VIDES for b in elements)
    assert all(b["machines_ids"] == [] for b in elements)


def test_poser_des_donnees_fait_tomber_neutre(client_installe):
    client_installe.get(CHEMIN)

    reponse = client_installe.put(f"{CHEMIN}/echenillage", json=BAREME_CALIBRE)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["neutre"] is False
    assert reponse.json()["donnees"] == BAREME_CALIBRE["donnees"]


def test_calibrer_un_bareme_n_en_calibre_pas_un_autre(client_installe):
    """Les quatre lignes partagent la meme valeur neutre a la creation : si
    elle etait partagee en memoire, en calibrer une les calibrerait toutes."""
    client_installe.put(f"{CHEMIN}/echenillage", json=BAREME_CALIBRE)

    elements = client_installe.get(CHEMIN).json()["elements"]

    par_type = {b["type"]: b for b in elements}
    assert par_type["echenillage"]["neutre"] is False
    assert all(par_type[t]["neutre"] is True for t in TYPES_ATTENDUS if t != "echenillage")


def test_vider_les_donnees_ramene_le_bareme_en_neutre(client_installe):
    """Consequence assumee du calcul : un bareme vide n'est plus calibre, et le
    front doit le dire — sinon il presenterait des scores indicatifs comme des
    scores regles."""
    client_installe.put(f"{CHEMIN}/echenillage", json=BAREME_CALIBRE)
    vide = dict(BAREME_CALIBRE)
    vide["donnees"] = DONNEES_VIDES

    reponse = client_installe.put(f"{CHEMIN}/echenillage", json=vide)

    assert reponse.json()["neutre"] is True


def test_un_type_inconnu_rend_introuvable(client_installe):
    reponse = client_installe.put(f"{CHEMIN}/gaufrage", json=BAREME_CALIBRE)

    assert reponse.status_code == 404, reponse.text
    assert reponse.json()["code"] == "introuvable"


def test_machines_ids_vide_est_valide_et_signifie_toutes(client_installe):
    corps = dict(BAREME_CALIBRE)
    corps["machines_ids"] = []

    reponse = client_installe.put(f"{CHEMIN}/effet_banane", json=corps)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["machines_ids"] == []


def test_une_machine_existante_est_acceptee(client_installe):
    identifiant = creer_machine(client_installe)
    corps = dict(BAREME_CALIBRE)
    corps["machines_ids"] = [identifiant]

    reponse = client_installe.put(f"{CHEMIN}/confort_roulage", json=corps)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["machines_ids"] == [identifiant]


def test_une_machine_inconnue_est_un_champ_fautif(client_installe):
    """Un bareme restreint a une machine qui n'existe pas serait silencieusement
    inapplicable, et personne ne verrait pourquoi les scores ne bougent plus."""
    corps = dict(BAREME_CALIBRE)
    corps["machines_ids"] = [999999]

    reponse = client_installe.put(f"{CHEMIN}/echenillage", json=corps)

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"
    assert "machines_ids" in reponse.json()["detail"]


def test_le_type_et_neutre_renvoyes_sont_IGNORES(client_installe):
    """Le front repose l'objet qu'il vient de lire. Refuser `type` et `neutre`
    l'obligerait a amputer son corps — un detail qu'un front oublie une fois sur
    deux, et qui produit un 422 incomprehensible. C'est l'URL qui porte le type,
    et `donnees` qui decide de `neutre`."""
    lu = client_installe.get(CHEMIN).json()["elements"][0]
    repose = dict(lu)
    repose["donnees"] = BAREME_CALIBRE["donnees"]
    repose["neutre"] = True
    repose["type"] = "effet_banane"

    reponse = client_installe.put(f"{CHEMIN}/echenillage", json=repose)

    assert reponse.status_code == 200, reponse.text
    # L'URL a gagne sur le corps, et `neutre` a ete recalcule.
    assert reponse.json()["type"] == "echenillage"
    assert reponse.json()["neutre"] is False
    assert client_installe.get(CHEMIN).json()["elements"][1]["neutre"] is True


def test_un_champ_inconnu_est_refuse(client_installe):
    corps = dict(BAREME_CALIBRE)
    corps["couleur_de_la_courbe"] = "bleu"

    reponse = client_installe.put(f"{CHEMIN}/echenillage", json=corps)

    assert reponse.status_code == 422, reponse.text


def test_sans_session_c_est_refuse(client_installe):
    client_installe.cookies.clear()

    reponse = client_installe.get(CHEMIN)

    assert reponse.status_code == 401, reponse.text
    assert reponse.json()["code"] == "session_absente"


def test_en_mode_demo_l_ecriture_est_refusee_mais_pas_la_lecture(
    client_installe, monkeypatch
):
    client_installe.get(CHEMIN)
    monkeypatch.setattr("app.dependances.DEMO_MODE", True)

    ecriture = client_installe.put(f"{CHEMIN}/echenillage", json=BAREME_CALIBRE)
    lecture = client_installe.get(CHEMIN)

    assert ecriture.status_code == 403, ecriture.text
    assert ecriture.json()["code"] == "mode_demo_lecture_seule"
    assert lecture.status_code == 200, lecture.text
