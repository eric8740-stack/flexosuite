# -*- coding: utf-8 -*-
"""Toute erreur sort au format du contrat : `{"code", "detail"}`.

Y compris celles que le framework leve tout seul. Une seule reponse d'une autre
forme oblige le front a ecrire un cas particulier — et c'est ce cas particulier
qui finira par diverger.
"""


def test_une_route_inconnue_sort_au_bon_format(client):
    r = client.get("/api/nexiste-pas")
    assert r.status_code == 404
    assert r.json() == {"code": "introuvable", "detail": r.json()["detail"]}
    assert r.json()["detail"]


def test_un_payload_invalide_nomme_les_champs(client):
    """`detail` est destine a un humain : il doit dire OU chercher."""
    r = client.post("/api/installation", json={"identifiant": "atelier"})
    assert r.status_code == 422
    corps = r.json()
    assert corps["code"] == "payload_invalide"
    assert "mot_de_passe" in corps["detail"]


def test_toute_erreur_porte_les_deux_champs(client):
    """Le front aiguille sur `code`, l'humain lit `detail`. Jamais l'un sans
    l'autre : un code sans texte ne s'affiche pas, un texte sans code
    n'aiguille pas."""
    for reponse in (
        client.get("/api/nexiste-pas"),
        client.post("/api/installation", json={}),
        client.get("/api/auth/moi"),
    ):
        corps = reponse.json()
        assert set(corps) == {"code", "detail"}, corps
        assert corps["code"] and corps["detail"]
