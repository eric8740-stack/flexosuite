# -*- coding: utf-8 -*-
"""Ce que les SIX referentiels doivent faire pareil.

Un seul routeur les sert tous : ces tests sont donc parametres sur les six, et
c'est voulu. Le defaut que cherche ce fichier n'est pas « la pagination est-elle
juste ? » mais « la pagination est-elle juste PARTOUT ? » — une correction
appliquee a cinq ressources sur six ne se voit pas a la relecture, et se
decouvre chez le client le jour ou un referentiel depasse un ecran.
"""
import pytest

from tests.aide_referentiels import CYLINDRES, MACHINES, TOUTES, corps_complet

# Volontairement recopiee du contrat, et NON importee du routeur : un test qui
# lit la borne dans le code qu'il verifie ne verifie plus rien.
TAILLE_MAXI = 200


def _creer(client, cas, suffixe=""):
    reponse = client.post(cas.chemin, json=corps_complet(client, cas, suffixe))
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


# --- L'enveloppe de liste et la pagination ----------------------------------


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_la_liste_vide_rend_l_enveloppe_et_pas_un_tableau_nu(client_installe, cas):
    reponse = client_installe.get(cas.chemin)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json() == {"elements": [], "total": 0}


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_le_total_compte_TOUT_et_pas_seulement_la_page(client_installe, cas):
    """Le piege classique : rendre `len(elements)` comme total. La liste
    paraitrait complete et la pagination du front disparaitrait."""
    for suffixe in ("", "-2", "-3"):
        _creer(client_installe, cas, suffixe)

    reponse = client_installe.get(cas.chemin, params={"taille": 2})

    corps = reponse.json()
    assert len(corps["elements"]) == 2
    assert corps["total"] == 3


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_les_pages_se_suivent_dans_l_ordre_des_identifiants(client_installe, cas):
    """Deux pages couvrent tout, sans doublon, et dans l'ordre annonce.

    ⚠️ **Limite MESUREE de ce test, et elle est ecrite ici pour qu'on ne le
    croie pas plus fort qu'il n'est.** Au banc de mutations, retirer
    `.order_by(...)` du routeur ne le fait PAS rougir : sur SQLite, l'ordre
    naturel d'un `SELECT` sans tri coincide avec l'ordre des identifiants tant
    qu'aucune ligne n'a ete reinseree. Ce test attrape un ordre explicite FAUX
    (tri descendant, tri sur un libelle — mutation verifiee rouge), pas un ordre
    ABSENT. Contre l'absence, il n'y a que le commentaire du routeur.
    """
    crees = [_creer(client_installe, cas, suffixe)["id"] for suffixe in ("", "-2", "-3")]

    page1 = client_installe.get(cas.chemin, params={"page": 1, "taille": 2}).json()
    page2 = client_installe.get(cas.chemin, params={"page": 2, "taille": 2}).json()

    identifiants = [e["id"] for e in page1["elements"] + page2["elements"]]
    assert identifiants == sorted(crees)


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_la_taille_maxi_passe_et_au_dela_est_refuse(client_installe, cas):
    """La borne est dans le contrat : 200 au plus, au-dela 422."""
    accepte = client_installe.get(cas.chemin, params={"taille": TAILLE_MAXI})
    refuse = client_installe.get(cas.chemin, params={"taille": TAILLE_MAXI + 1})

    assert accepte.status_code == 200, accepte.text
    assert refuse.status_code == 422, refuse.text
    assert refuse.json()["code"] == "payload_invalide"


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_la_page_zero_est_refusee(client_installe, cas):
    reponse = client_installe.get(cas.chemin, params={"page": 0})

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"


# --- `actif` : on desactive, on ne cache pas --------------------------------


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_un_element_desactive_reste_lisible_et_liste(client_installe, cas):
    """Pas de filtre cache. C'est l'optimisation (lot 2c) qui ignorera
    `actif = false` ; l'API, elle, ne fait pas disparaitre des lignes."""
    corps = dict(corps_complet(client_installe, cas))
    corps["actif"] = False
    cree = client_installe.post(cas.chemin, json=corps).json()

    unitaire = client_installe.get(f"{cas.chemin}/{cree['id']}")
    liste = client_installe.get(cas.chemin).json()

    assert unitaire.status_code == 200
    assert unitaire.json()["actif"] is False
    assert [e["id"] for e in liste["elements"]] == [cree["id"]]
    assert liste["total"] == 1


# --- Les quatre codes d'erreur ----------------------------------------------


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_la_cle_en_double_rend_deja_existant(client_installe, cas):
    """409 `deja_existant` sur la cle du contrat. Le MEME corps est poste deux
    fois : pour un cylindre, cela vise bien la meme machine, donc le couple
    (machine, repere) est reellement en conflit."""
    corps = corps_complet(client_installe, cas)
    premier = client_installe.post(cas.chemin, json=corps)
    assert premier.status_code == 201, premier.text

    second = client_installe.post(cas.chemin, json=corps)

    assert second.status_code == 409, second.text
    assert second.json()["code"] == "deja_existant"
    assert second.json()["detail"]


@pytest.mark.parametrize("cas", TOUTES, ids=str)
@pytest.mark.parametrize("methode", ["get", "put", "delete"])
def test_un_identifiant_inconnu_rend_introuvable(client_installe, cas, methode):
    chemin = f"{cas.chemin}/999999"
    appel = getattr(client_installe, methode)
    reponse = (
        appel(chemin, json=corps_complet(client_installe, cas))
        if methode == "put"
        else appel(chemin)
    )

    assert reponse.status_code == 404, reponse.text
    assert reponse.json()["code"] == "introuvable"


# --- Les gardes --------------------------------------------------------------


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_sans_session_la_lecture_est_refusee(client_installe, cas):
    """401, pas 403 : le front redirige vers la connexion sans perdre la
    saisie en cours."""
    client_installe.cookies.clear()

    reponse = client_installe.get(cas.chemin)

    assert reponse.status_code == 401, reponse.text
    assert reponse.json()["code"] == "session_absente"


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_en_mode_demo_l_ecriture_est_refusee(client_installe, cas, monkeypatch):
    """403 `mode_demo_lecture_seule`. Le drapeau est corrige sur
    `app.dependances`, pas sur `app.config` : la valeur y est liee A L'IMPORT,
    et corriger la source ne changerait rien a ce que la garde lit."""
    corps = corps_complet(client_installe, cas)
    monkeypatch.setattr("app.dependances.DEMO_MODE", True)

    reponse = client_installe.post(cas.chemin, json=corps)

    assert reponse.status_code == 403, reponse.text
    assert reponse.json()["code"] == "mode_demo_lecture_seule"


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_en_mode_demo_la_lecture_reste_ouverte(client_installe, cas, monkeypatch):
    """Le contre-test : une garde qui refuserait TOUT passerait le test
    precedent sans rien prouver."""
    monkeypatch.setattr("app.dependances.DEMO_MODE", True)

    reponse = client_installe.get(cas.chemin)

    assert reponse.status_code == 200, reponse.text


# --- Remplacement et suppression --------------------------------------------


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_le_put_remplace_et_rend_le_corps_complet(client_installe, cas):
    corps = corps_complet(client_installe, cas)
    cree = client_installe.post(cas.chemin, json=corps).json()
    modifie = dict(corps)
    modifie["actif"] = False

    reponse = client_installe.put(f"{cas.chemin}/{cree['id']}", json=modifie)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["id"] == cree["id"]
    assert reponse.json()["actif"] is False
    assert set(reponse.json()) == set(cas.cles_attendues)


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_le_put_refuse_un_corps_INCOMPLET(client_installe, cas):
    """Constat 1 de l'audit du 16/09/2026 — le défaut que ce test aurait attrapé.

    Un champ REQUIS omis rendait deja 422. Mais les champs porteurs d'une valeur
    par defaut — `actif`, `modules`, `contact`, `forme_speciale`... — etaient
    silencieusement REINITIALISES : un `PUT` qui oubliait `actif` reactivait un
    element desactive, sans erreur et sans trace.

    C'est la regle « on ne supprime pas, on desactive » qu'un enregistrement
    distrait defaisait — celle-la meme qui protege l'histoire des devis deja
    envoyes a des clients.

    « Remplacement complet » doit donc vouloir dire complet **pour tous les
    champs**, pas seulement pour les obligatoires.
    """
    corps = corps_complet(client_installe, cas)
    cree = client_installe.post(cas.chemin, json=corps).json()
    champs_a_defaut = [c for c in cas.cles_attendues if c not in corps and c != "id"]
    assert "actif" in corps, "le corps de reference doit porter `actif`"

    for champ in ["actif", *champs_a_defaut]:
        ampute = {c: v for c, v in corps.items() if c != champ}
        reponse = client_installe.put(f"{cas.chemin}/{cree['id']}", json=ampute)

        assert reponse.status_code == 422, f"{champ} omis -> {reponse.status_code}"
        assert reponse.json()["code"] == "payload_invalide"
        assert champ in reponse.json()["detail"], champ


def test_le_put_incomplet_ne_reactive_pas_un_element_desactive(client_installe):
    """La conséquence métier du constat 1, verifiee de bout en bout."""
    corps = dict(corps_complet(client_installe, MACHINES))
    corps["actif"] = False
    cree = client_installe.post(MACHINES.chemin, json=corps).json()
    ampute = {c: v for c, v in corps.items() if c not in ("actif", "modules")}

    client_installe.put(f"{MACHINES.chemin}/{cree['id']}", json=ampute)

    relu = client_installe.get(f"{MACHINES.chemin}/{cree['id']}").json()
    assert relu["actif"] is False
    assert relu["modules"] == corps["modules"]


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_le_put_accepte_null_sur_un_champ_nullable_present(client_installe, cas):
    """Le contre-test : « tous les champs obligatoires » ne veut pas dire « tous
    les champs non nuls ». Un champ nullable doit etre PRESENT, sa valeur peut
    etre `null` — sinon on ne pourrait plus effacer un email."""
    corps = dict(corps_complet(client_installe, cas))
    cree = client_installe.post(cas.chemin, json=corps).json()
    nullables = [c for c, v in corps.items() if v is None]
    if not nullables:
        pytest.skip("cette ressource n'a aucun champ nullable dans le corps de demo")

    reponse = client_installe.put(f"{cas.chemin}/{cree['id']}", json=corps)

    assert reponse.status_code == 200, reponse.text
    assert all(reponse.json()[c] is None for c in nullables)


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_le_put_sur_soi_meme_ne_declenche_pas_deja_existant(client_installe, cas):
    """Enregistrer un formulaire sans toucher a la cle ne doit pas se heurter a
    sa propre valeur — sinon plus aucune modification ne passe."""
    corps = corps_complet(client_installe, cas)
    cree = client_installe.post(cas.chemin, json=corps).json()

    reponse = client_installe.put(f"{cas.chemin}/{cree['id']}", json=corps)

    assert reponse.status_code == 200, reponse.text


@pytest.mark.parametrize("cas", TOUTES, ids=str)
def test_la_suppression_d_un_element_libre_rend_204(client_installe, cas):
    corps = corps_complet(client_installe, cas)
    cree = client_installe.post(cas.chemin, json=corps).json()

    reponse = client_installe.delete(f"{cas.chemin}/{cree['id']}")

    assert reponse.status_code == 204, reponse.text
    assert reponse.content == b""
    assert client_installe.get(f"{cas.chemin}/{cree['id']}").status_code == 404


def test_une_cle_en_double_sur_une_AUTRE_machine_passe(client_installe):
    """Le repere d'un cylindre est grave sur SA machine : deux presses ont
    chacune leur « A3 ». Une unicite posee sur le seul repere casserait un parc
    reel des la deuxieme presse."""
    premier = corps_complet(client_installe, CYLINDRES)
    assert client_installe.post(CYLINDRES.chemin, json=premier).status_code == 201
    second = dict(premier)
    second["machine_id"] = client_installe.post(
        MACHINES.chemin, json=dict(corps_complet(client_installe, MACHINES, "-bis"))
    ).json()["id"]

    reponse = client_installe.post(CYLINDRES.chemin, json=second)

    assert reponse.status_code == 201, reponse.text
    assert reponse.json()["repere_machine"] == premier["repere_machine"]
