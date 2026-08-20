# -*- coding: utf-8 -*-
"""`Secure` est un REGLAGE, mais son defaut est « actif ».

La demo publique est en HTTPS et l'exige ; le package client tourne en HTTP sur
le reseau de l'imprimerie et serait sinon inutilisable. La derogation doit donc
etre possible — mais **explicite**. Un defaut permissif finirait livre sur la
demo publique sans que personne ne le remarque.

Les tests d'API tournent avec `COOKIE_SECURE=0` (cf. `conftest.py`), ce qui est
exactement le reglage du package. C'est pourquoi le DEFAUT a besoin de son
propre test : sans lui, plus rien ne le verifierait.
"""
import importlib
import sys


def _recharger_config(monkeypatch, valeur):
    if valeur is None:
        monkeypatch.delenv("COOKIE_SECURE", raising=False)
    else:
        monkeypatch.setenv("COOKIE_SECURE", valeur)
    sys.modules.pop("app.config", None)
    return importlib.import_module("app.config")


def test_actif_quand_rien_n_est_regle(monkeypatch):
    assert _recharger_config(monkeypatch, None).COOKIE_SECURE is True


def test_desactivable_explicitement(monkeypatch):
    """C'est le cas du package client : HTTP sur le reseau de l'imprimerie."""
    assert _recharger_config(monkeypatch, "0").COOKIE_SECURE is False


def test_toute_autre_valeur_laisse_secure_actif(monkeypatch):
    """`COOKIE_SECURE=faux` ou une faute de frappe ne doit pas ouvrir la porte :
    seul `0` desactive."""
    assert _recharger_config(monkeypatch, "faux").COOKIE_SECURE is True
    _recharger_config(monkeypatch, "0")  # etat des tests d'API


def test_la_duree_par_defaut_est_de_douze_heures(monkeypatch):
    monkeypatch.delenv("SESSION_DUREE_H", raising=False)
    sys.modules.pop("app.config", None)
    assert importlib.import_module("app.config").SESSION_DUREE_H == 12
    _recharger_config(monkeypatch, "0")
