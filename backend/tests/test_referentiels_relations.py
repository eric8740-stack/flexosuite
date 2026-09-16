# -*- coding: utf-8 -*-
"""Ce qui lie les referentiels entre eux — et ce que ca interdit.

Deux regles du contrat v1.2 se jouent ici :

- **on ne supprime pas ce qui sert** (409 `reference_utilisee`), et le message
  propose la desactivation ;
- **un identifiant qui ne designe rien est un champ fautif** (422), pas un
  endpoint absent.

Les deux relations livrees au lot 2b sont machine -> cylindre et
cylindre -> outil. Le lot 2c ajoutera les devis en etendant `LIENS` dans
`app/services/referentiels.py` — pas en ecrivant une deuxieme fonction.
"""
import pytest

from tests.aide_referentiels import (
    CYLINDRES,
    MACHINES,
    OUTILS,
    corps_complet,
    creer_cylindre,
    creer_machine,
)


def test_une_machine_portee_par_un_cylindre_ne_se_supprime_pas(client_installe):
    corps = corps_complet(client_installe, CYLINDRES)
    assert client_installe.post(CYLINDRES.chemin, json=corps).status_code == 201

    reponse = client_installe.delete(f"{MACHINES.chemin}/{corps['machine_id']}")

    assert reponse.status_code == 409, reponse.text
    assert reponse.json()["code"] == "reference_utilisee"


def test_un_cylindre_porte_par_un_outil_ne_se_supprime_pas(client_installe):
    corps = corps_complet(client_installe, OUTILS)
    assert client_installe.post(OUTILS.chemin, json=corps).status_code == 201

    reponse = client_installe.delete(f"{CYLINDRES.chemin}/{corps['cylindre_id']}")

    assert reponse.status_code == 409, reponse.text
    assert reponse.json()["code"] == "reference_utilisee"


def test_le_refus_propose_la_desactivation(client_installe):
    """Le `detail` s'adresse a un deviseur. Une erreur qui dit seulement « non »
    le laisse sans geste suivant, et il contourne — en renommant l'element, ce
    qui abime les devis passes au lieu de les effacer franchement."""
    corps = corps_complet(client_installe, CYLINDRES)
    client_installe.post(CYLINDRES.chemin, json=corps)

    detail = client_installe.delete(
        f"{MACHINES.chemin}/{corps['machine_id']}"
    ).json()["detail"]

    assert "esactiv" in detail


def test_la_machine_redevient_supprimable_une_fois_le_cylindre_parti(
    client_installe,
):
    """Le contre-test du refus : une garde qui refuserait TOUJOURS passerait
    les trois tests precedents sans rien prouver."""
    corps = corps_complet(client_installe, CYLINDRES)
    cylindre = client_installe.post(CYLINDRES.chemin, json=corps).json()
    assert (
        client_installe.delete(f"{MACHINES.chemin}/{corps['machine_id']}").status_code
        == 409
    )

    client_installe.delete(f"{CYLINDRES.chemin}/{cylindre['id']}")
    reponse = client_installe.delete(f"{MACHINES.chemin}/{corps['machine_id']}")

    assert reponse.status_code == 204, reponse.text


def test_une_machine_libre_se_supprime(client_installe):
    identifiant = creer_machine(client_installe)

    reponse = client_installe.delete(f"{MACHINES.chemin}/{identifiant}")

    assert reponse.status_code == 204, reponse.text


@pytest.mark.parametrize(
    "cas,champ",
    [(CYLINDRES, "machine_id"), (OUTILS, "cylindre_id")],
    ids=["cylindre-machine", "outil-cylindre"],
)
def test_une_cle_etrangere_inconnue_est_un_champ_fautif(client_installe, cas, champ):
    """422 et non 404 : le contrat se sert deja du 404 pour « cet endpoint
    n'est pas encore livre ». Un front qui recoit 404 sur un POST ne saurait
    pas s'il doit surligner un champ ou renoncer a l'ecran."""
    corps = dict(corps_complet(client_installe, cas))
    corps[champ] = 999999

    reponse = client_installe.post(cas.chemin, json=corps)

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"
    assert champ in reponse.json()["detail"]


def test_le_put_verifie_aussi_la_cle_etrangere(client_installe):
    """Le defaut classique : la creation controle, la modification non."""
    corps = corps_complet(client_installe, CYLINDRES)
    cree = client_installe.post(CYLINDRES.chemin, json=corps).json()
    modifie = dict(corps)
    modifie["machine_id"] = 999999

    reponse = client_installe.put(f"{CYLINDRES.chemin}/{cree['id']}", json=modifie)

    assert reponse.status_code == 422, reponse.text
    assert reponse.json()["code"] == "payload_invalide"


def test_une_suppression_refusee_par_la_BASE_rend_409_et_pas_500(
    client_installe, monkeypatch
):
    """Point 7 de l'audit du 16/09/2026 — le défaut que ce test aurait attrapé.

    `est_reference()` est une garde APPLICATIVE : elle lit, puis on supprime. Si
    une ligne fille apparait entre les deux, c'est SQLite qui refuse, et le
    `commit` n'etait protege par rien — l'appelant recevait **500** alors que le
    contrat a un code exact pour ce cas.

    La course est etroite sur un poste mono-utilisateur ; la demo publique, elle,
    n'est pas mono-utilisateur. On la simule en neutralisant la garde
    applicative : la contrainte de la base reste, et c'est elle qu'on exerce.
    """
    corps = corps_complet(client_installe, CYLINDRES)
    client_installe.post(CYLINDRES.chemin, json=corps)
    monkeypatch.setattr("app.routers.referentiels.est_reference", lambda db, e: None)

    reponse = client_installe.delete(f"{MACHINES.chemin}/{corps['machine_id']}")

    assert reponse.status_code == 409, reponse.text
    assert reponse.json()["code"] == "reference_utilisee"


def test_un_outil_peut_pointer_un_cylindre_desactive(client_installe):
    """`actif = false` n'est pas une suppression : l'element reste utilisable
    en lecture et en reference. C'est l'optimisation du lot 2c qui l'ecartera,
    pas l'integrite des donnees."""
    identifiant = creer_cylindre(client_installe)
    cylindre = client_installe.get(f"{CYLINDRES.chemin}/{identifiant}").json()
    desactive = {c: cylindre[c] for c in cylindre if c != "id"}
    desactive["actif"] = False
    client_installe.put(f"{CYLINDRES.chemin}/{identifiant}", json=desactive)

    corps = dict(OUTILS.corps)
    corps["cylindre_id"] = identifiant
    reponse = client_installe.post(OUTILS.chemin, json=corps)

    assert reponse.status_code == 201, reponse.text
