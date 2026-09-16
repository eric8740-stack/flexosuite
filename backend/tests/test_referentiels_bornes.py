# -*- coding: utf-8 -*-
"""Les bornes des referentiels — section 5 du contrat.

⚠️ **Ce fichier ne corrige RIEN, et c'est son resultat.**

La demande etait « bornes section 5 », sur le modele du constat 1 de l'audit
(section 6, ou rien n'etait borne). La **mesure** a dit autre chose : la section 5
etait deja bornee, champ par champ, des son ecriture. Les 27 tests ci-dessous
etaient **verts avant** d'etre ecrits — il n'y a pas eu de phase rouge, parce
qu'il n'y avait pas de defaut.

Sondage prealable des 23 champs numeriques : deux seulement laissaient passer un
negatif au niveau du **schema**, `machine_id` et `cylindre_id`. Mais l'API, elle,
rendait deja **422 `payload_invalide`** en nommant le champ — la recherche de la
cle etrangere ne trouve rien, et aucun identifiant negatif ne peut correspondre a
une cle primaire auto-incrementee. Le comportement observable etait donc **deja
correct**, et y ajouter `gt=0` n'aurait rien change de visible. Ce n'est pas fait.

Ce que ces tests apportent alors : ils **verrouillent** les bornes. Verifie en
retirant trois d'entre elles (`prix_m2_eur`, `coefficient_vitesse`,
`nb_porte_cliches`) — **4 tests rouges**, dont celui du `PUT`. Ils ne sont donc
pas creux, et un assouplissement futur rougira.

Deux ecarts avec l'enonce des bornes, assumes et mesures :

- `client.intervalle_dev_min_mm` est une dimension, mais reste **≥ 0** et non
  « > 0 » : zero y signifie **pas de contrainte de pose**. L'interdire obligerait
  tout client sans contrainte a inventer une valeur.
- `outil.nb_poses_laize` et `nb_poses_developpe` sont des compteurs `nb_*`, mais
  restent **> 0** et non « ≥ 0 » : un outil sans pose n'existe pas. C'est plus
  strict que demande ; relacher serait une regression.
"""
import pytest

from tests.aide_referentiels import TOUTES, corps_complet

# Les cas de ressource, adressables par le chemin du contrat.
PAR_CHEMIN = {cas.chemin: cas for cas in TOUTES}

# --- Les cles etrangeres ------------------------------------------------------
# Un identifiant designe une ligne : zero et le negatif n'en designent aucune.
# Le schema ne les borne pas, mais la recherche en base rend 422 en nommant le
# champ — et aucun identifiant negatif ne peut correspondre a une cle primaire
# auto-incrementee. Ces tests figent le COMPORTEMENT (422 + champ nomme), pas son
# mecanisme : poser `gt=0` demain les laisserait verts, et c'est voulu.
CLES_ETRANGERES = (
    ("/api/cylindres", "machine_id"),
    ("/api/outils", "cylindre_id"),
)


@pytest.mark.parametrize(("chemin", "champ"), CLES_ETRANGERES)
@pytest.mark.parametrize("valeur", [0, -1])
def test_une_cle_etrangere_NULLE_OU_NEGATIVE_est_refusee(
    client_installe, chemin, champ, valeur
):
    corps = dict(_corps_valide(client_installe, chemin))
    corps[champ] = valeur

    reponse = client_installe.post(chemin, json=corps)

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"
    assert champ in reponse.json()["detail"]


# --- Dimensions, coefficients, prix, temps, compteurs -------------------------
# Toutes deja en place. Ecrites pour qu'un assouplissement futur rougisse.

STRICTEMENT_POSITIFS = (
    ("/api/machines", "laize_utile_mm", "0"),
    ("/api/machines", "laize_maxi_mm", "0"),
    ("/api/machines", "vitesse_moyenne_m_h", 0),
    ("/api/machines", "diametre_bobine_maxi_mm", "0"),
    ("/api/cylindres", "developpe_mm", "0"),
    ("/api/matieres", "grammage_g_m2", "0"),
    ("/api/matieres", "epaisseur_reelle_micron", 0),
    ("/api/outils", "largeur_mm", "0"),
    ("/api/outils", "hauteur_mm", "0"),
    ("/api/outils", "nb_poses_laize", 0),
    ("/api/outils", "nb_poses_developpe", 0),
    ("/api/options", "coefficient_vitesse", "0"),
    ("/api/options", "coefficient_gache", "0"),
)


@pytest.mark.parametrize(("chemin", "champ", "zero"), STRICTEMENT_POSITIFS)
def test_une_dimension_ou_un_coefficient_NUL_est_refuse(
    client_installe, chemin, champ, zero
):
    """Dimensions, developpe, laize, vitesse, grammage, epaisseur, coefficients.

    Zero n'est pas « pas de valeur » : une laize nulle, une vitesse nulle ou un
    coefficient nul rendraient le devis absurde — un coefficient de vitesse a
    zero annulerait la vitesse de toute la configuration, puisqu'ils se cumulent
    multiplicativement.
    """
    corps = dict(_corps_valide(client_installe, chemin))
    corps[champ] = zero

    reponse = client_installe.post(chemin, json=corps)

    assert reponse.status_code == 422, reponse.text
    assert champ in reponse.json()["detail"]


POSITIFS_OU_NULS = (
    ("/api/machines", "duree_calage_h", "-1.00"),
    ("/api/machines", "temps_changement_bobine_h", "-1.00"),
    ("/api/machines", "nb_groupes_couleurs", -1),
    ("/api/cylindres", "nb_porte_cliches", -1),
    ("/api/matieres", "prix_m2_eur", "-1.0000"),
    ("/api/clients", "intervalle_dev_min_mm", "-1.00"),
    ("/api/options", "temps_calage_ajoute_h", "-1.00"),
    ("/api/options", "groupes_couleurs_requis", -1),
)


@pytest.mark.parametrize(("chemin", "champ", "negatif"), POSITIFS_OU_NULS)
def test_un_prix_un_temps_ou_un_compteur_NEGATIF_est_refuse(
    client_installe, chemin, champ, negatif
):
    """Prix ≥ 0, temps ≥ 0, compteurs `nb_*` ≥ 0. Zero reste legitime : un poste
    peut ne rien couter, un calage peut etre instantane, un cylindre peut n'avoir
    aucun porte-cliches."""
    corps = dict(_corps_valide(client_installe, chemin))
    corps[champ] = negatif

    reponse = client_installe.post(chemin, json=corps)

    assert reponse.status_code == 422, reponse.text
    assert champ in reponse.json()["detail"]


def test_le_prix_et_le_calage_a_ZERO_restent_acceptes(client_installe):
    """Le controle dans l'autre sens : la borne est ≥ 0, pas > 0.

    Sans ce test, resserrer `prix_m2_eur` en `gt=0` passerait inapercu et
    interdirait une matiere fournie par le client.
    """
    corps = dict(_corps_valide(client_installe, "/api/matieres"))
    corps["nom"] = "Support fourni par le client"
    corps["prix_m2_eur"] = "0.0000"

    reponse = client_installe.post("/api/matieres", json=corps)

    assert reponse.status_code == 201, reponse.text
    assert reponse.json()["prix_m2_eur"] == "0.0000"


def test_la_borne_vaut_AUSSI_au_PUT(client_installe):
    """Les schemas de `PUT` sont DERIVES des schemas d'ecriture (`remplacement()`).

    La derivation ne retire que les valeurs par defaut — mais rien ne le
    garantissait par un test. Si elle perdait les contraintes en chemin, le
    `POST` serait borne et le `PUT` ne le serait plus : la porte de derriere.
    """
    cree = client_installe.post(
        "/api/matieres", json=_corps_valide(client_installe, "/api/matieres")
    )
    assert cree.status_code == 201, cree.text

    corps = dict(cree.json())
    corps.pop("id")
    corps["prix_m2_eur"] = "-1.0000"

    reponse = client_installe.put(f"/api/matieres/{cree.json()['id']}", json=corps)

    assert reponse.status_code == 422, reponse.text
    assert "prix_m2_eur" in reponse.json()["detail"]


def _corps_valide(client, chemin: str) -> dict:
    """Un corps ACCEPTE, dont chaque test ne modifie qu'un seul champ.

    Passe par `corps_complet` : il resout la cle etrangere en creant le parent.
    Sans cela, un cylindre sonde sur `developpe_mm` echouerait sur son
    `machine_id` et le test serait vert pour la mauvaise raison.
    """
    return corps_complet(client, PAR_CHEMIN[chemin])
