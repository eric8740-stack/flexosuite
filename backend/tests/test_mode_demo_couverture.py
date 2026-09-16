# -*- coding: utf-8 -*-
"""Aucune route d'ecriture n'echappe au mode demo sans etre NOMMEE ici.

Constat 8 de l'audit du 16/09/2026 — celui que l'exploration a trouve.

`routers/calibration.py` omet volontairement `interdire_ecriture_demo`, et
l'argument est juste **pour la route d'aujourd'hui** : `POST
/api/calibration/taux-machine` ne prend pas de session de base, il ne peut rien
ecrire. Le defaut n'est pas la.

⚠️ **L'exemption vit sur le ROUTEUR, alors que sa justification porte sur la
ROUTE.** `APIRouter(dependencies=[...])` s'applique a tout ce qu'on lui ajoute
ensuite : un futur `POST /api/calibration/appliquer` qui ecrirait serait
accessible en mode demo **en silence**. Le commentaire du routeur dit « le jour
ou cet endpoint ecrira, la garde doit revenir » — mais rien ne le faisait
tomber.

Ce fichier le fait tomber. Ajouter une route d'ecriture a un routeur exempte
devient **rouge**, et le seul moyen de la rendre verte est de l'inscrire
ci-dessous avec son motif — c'est-a-dire d'y penser.

⚠️ **On teste le COMPORTEMENT, pas le cablage.** Une premiere version lisait les
dependances dans les objets de routage de FastAPI : elle dependait d'attributs
internes (`_IncludedRouter`, `dependant`) qui ont deja change de forme entre
deux versions, et elle mesurait la plomberie plutot que la promesse. Ici, on
appelle chaque route et on regarde ce qu'elle repond. C'est ce que le contrat
promet, et c'est vrai quelle que soit la facon dont la garde est branchee.
"""
import pytest

from app.main import app

METHODES_ECRITURE = {"POST", "PUT", "PATCH", "DELETE"}

# Les routes d'ecriture qui echappent DELIBEREMENT au mode demo. Chaque entree
# porte son motif : une exemption sans motif est une exemption que personne ne
# saura relire.
EXEMPTIONS_ASSUMEES = {
    # Fonction PURE : aucune session de base, aucune ligne touchee. La refuser
    # retirerait a la demonstration publique l'ecran qui montre le mieux
    # l'application, sans rien proteger.
    ("POST", "/api/calibration/taux-machine"),
    # L'installation precede l'existence meme du mode demo.
    ("POST", "/api/installation"),
    # Se connecter et se deconnecter n'ecrit pas de donnee metier, et une demo
    # ou l'on ne peut pas ouvrir de session ne se visite pas.
    ("POST", "/api/auth/connexion"),
    ("POST", "/api/auth/deconnexion"),
}


def _routes_d_ecriture() -> list[tuple[str, str]]:
    """Depuis le schema OpenAPI : c'est la surface PUBLIQUE de l'application."""
    schema = app.openapi()
    return sorted(
        (methode.upper(), chemin)
        for chemin, operations in schema["paths"].items()
        for methode in operations
        if methode.upper() in METHODES_ECRITURE
    )


def _appeler(client, methode: str, chemin: str):
    # Un identifiant quelconque : la garde du mode demo passe AVANT la lecture
    # de la ressource et avant la validation du corps. Si elle repond, elle
    # repond sans rien chercher.
    url = chemin.replace("{id_element}", "1").replace("{type_bareme}", "echenillage")
    return client.request(methode, url, json={})


@pytest.mark.parametrize(
    ("methode", "chemin"),
    [c for c in _routes_d_ecriture() if c not in EXEMPTIONS_ASSUMEES],
)
def test_une_route_d_ecriture_repond_403_en_mode_demo(
    client_installe, monkeypatch, methode, chemin
):
    monkeypatch.setattr("app.dependances.DEMO_MODE", True)

    reponse = _appeler(client_installe, methode, chemin)

    assert reponse.status_code == 403, (
        f"{methode} {chemin} a repondu {reponse.status_code} en mode demo. "
        "Soit la garde manque, soit l'exemption doit etre inscrite AVEC SON "
        "MOTIF dans EXEMPTIONS_ASSUMEES."
    )


def test_aucune_exemption_ne_survit_a_la_route_qu_elle_designait():
    """Le controle dans l'autre sens.

    Une exemption dont la route a disparu — renommee, supprimee — resterait
    dans la liste et couvrirait en silence la prochaine route qui reprendrait ce
    chemin. Une liste d'exemptions ne se nettoie que si quelque chose l'y force.
    """
    perimees = EXEMPTIONS_ASSUMEES - set(_routes_d_ecriture())

    assert not perimees, (
        f"Exemptions qui ne designent plus aucune route : {sorted(perimees)}. "
        "A retirer, sinon elles couvriront la prochaine route de meme chemin."
    )


def test_le_controle_sait_dire_UN():
    """Sans ceci, le test parametre passerait sur une liste vide.

    Un controle qui n'a jamais rien vu ne prouve pas qu'il n'y a rien : il
    prouve qu'il ne regarde pas.
    """
    routes = _routes_d_ecriture()

    assert len(routes) > 15, routes
    assert ("POST", "/api/machines") in routes
    assert ("PUT", "/api/baremes/{type_bareme}") in routes
