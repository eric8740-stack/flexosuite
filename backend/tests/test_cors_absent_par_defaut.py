# -*- coding: utf-8 -*-
"""Le partage d'origine ne doit exister QU'EN DEVELOPPEMENT.

Les deux livrables — package Windows chez l'imprimeur, demo publique — tournent
en MONO-PORT : la page et l'API ont la meme origine, et aucune requete ne passe
par le partage d'origine. Un middleware actif « au cas ou » serait une
autorisation livree chez le client sans qu'il en ait besoin, et sans que
personne ne la remarque.

Constat de l'audit du 20/08/2026 : le squelette livrait un partage d'origine en
dur sur localhost:3000, avec transport des identifiants. Inutile dans les deux
livrables, et invisible.
"""
import importlib
import sys

import pytest
from starlette.middleware.cors import CORSMiddleware


def _recharger_app(monkeypatch, valeur: str | None):
    """Recharge le module avec un environnement donne.

    La configuration est lue a l'import : sans rechargement, on testerait
    l'etat fige au premier import et le test ne prouverait rien.
    """
    if valeur is None:
        monkeypatch.delenv("CORS_ORIGINES", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINES", valeur)
    for module in ("app.config", "app.main"):
        sys.modules.pop(module, None)
    return importlib.import_module("app.main")


def _a_du_partage_d_origine(application) -> bool:
    return any(m.cls is CORSMiddleware for m in application.user_middleware)


def test_absent_quand_rien_n_est_configure(monkeypatch):
    """C'est l'etat du package client et de la demo."""
    module = _recharger_app(monkeypatch, None)
    assert not _a_du_partage_d_origine(module.app)


def test_absent_quand_le_reglage_est_vide(monkeypatch):
    module = _recharger_app(monkeypatch, "   ")
    assert not _a_du_partage_d_origine(module.app)


def test_present_quand_des_origines_sont_listees(monkeypatch):
    """En developpement, le front tourne sur son propre port : la, il sert."""
    # Deux origines pour eprouver le decoupage, mais UN SEUL nom d'hote :
    # melanger `localhost` et `127.0.0.1` dans un exemple reviendrait a modeler
    # la mauvaise pratique — ce sont deux hotes differents pour same-site.
    module = _recharger_app(monkeypatch, "http://localhost:3000,http://localhost:3001")
    assert _a_du_partage_d_origine(module.app)
    assert module.CORS_ORIGINES == [
        "http://localhost:3000",
        "http://localhost:3001",
    ]


def test_l_etoile_est_refusee_au_demarrage(monkeypatch):
    """`*` avec un cookie de session est refuse par la specification, et serait
    de toute facon une porte ouverte. On echoue au demarrage plutot que de
    laisser un reglage dangereux passer inapercu."""
    with pytest.raises(RuntimeError, match="origines exactes"):
        _recharger_app(monkeypatch, "*")
    # On remet l'application dans un etat sain pour les tests suivants.
    _recharger_app(monkeypatch, None)
