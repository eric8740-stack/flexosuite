# -*- coding: utf-8 -*-
"""Le controle d'origine : la DEUXIEME serrure.

`SameSite=Strict` couvre deja l'essentiel. Ce controle existe pour le cas ou un
navigateur ancien, ou une extension, traiterait `SameSite` avec largesse.

Trois choix sont testes ici parce qu'ils sont contre-intuitifs et qu'une
relecture pressee les « corrigerait » :

- les LECTURES ne sont pas concernees — elles ne modifient rien ;
- une requete SANS en-tete `Origin` passe — elle ne vient pas d'un navigateur,
  donc aucun cookie n'est transporte a l'insu de quiconque ;
- l'origine du SERVICE est acceptee sans avoir a etre listee nulle part.
"""
from tests.conftest import IDENTIFIANT, MOT_DE_PASSE

CHARGE = {"identifiant": IDENTIFIANT, "mot_de_passe": MOT_DE_PASSE}


def test_une_ecriture_d_une_autre_origine_est_refusee(client):
    r = client.post("/api/installation", json=CHARGE, headers={"Origin": "http://mechant.example"})
    assert r.status_code == 403
    assert r.json()["code"] == "origine_refusee"


def test_l_origine_du_service_est_acceptee(client):
    r = client.post("/api/installation", json=CHARGE, headers={"Origin": "http://testserver"})
    assert r.status_code == 201


def test_sans_en_tete_origine_ca_passe(client):
    """Sinon les scripts du package et les tests seraient casses sans que rien
    ne soit protege de plus."""
    assert client.post("/api/installation", json=CHARGE).status_code == 201


def test_les_lectures_ne_sont_pas_concernees(client_installe):
    r = client_installe.get("/api/contexte", headers={"Origin": "http://mechant.example"})
    assert r.status_code == 200


def test_l_origine_refusee_ne_touche_pas_la_base(client):
    """Le refus doit tomber AVANT le traitement : une ecriture refusee qui a
    quand meme cree le compte serait pire que pas de controle du tout."""
    client.post("/api/installation", json=CHARGE, headers={"Origin": "http://mechant.example"})
    assert client.get("/api/contexte").json()["installation_faite"] is False
