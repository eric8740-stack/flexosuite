# -*- coding: utf-8 -*-
"""Socle des tests d'API.

⚠️ **L'ordre des instructions de ce fichier compte.** `app.config` lit
l'environnement A L'IMPORT : les variables doivent donc etre posees AVANT le
premier import de l'application. pytest importe `conftest.py` avant les modules
de test, ce qui rend ce placement fiable.

`COOKIE_SECURE=0` n'est pas un contournement : c'est exactement le reglage du
package client, qui tourne en HTTP sur le reseau de l'imprimerie. Sans lui, le
client de test — qui parle en `http://` — refuserait de renvoyer un cookie
`Secure`, et les tests de session echoueraient pour une raison qui n'a rien a
voir avec ce qu'ils verifient. Le defaut (`Secure` actif) a son propre test.
"""
import os
import tempfile

_DOSSIER = tempfile.mkdtemp(prefix="flexosuite-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_DOSSIER}/test.db".replace("\\", "/")
os.environ["COOKIE_SECURE"] = "0"
os.environ.pop("CORS_ORIGINES", None)
os.environ.pop("DEMO_MODE", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

IDENTIFIANT = "atelier"
MOT_DE_PASSE = "motdepasse-atelier"


@pytest.fixture(autouse=True)
def base_vierge():
    """Chaque test part d'une base vide : un test qui depend de l'ordre des
    autres finit par echouer seul, et on cherche ailleurs."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_installe(client):
    """Un client dont l'installation est faite et la session ouverte."""
    reponse = client.post(
        "/api/installation",
        json={"identifiant": IDENTIFIANT, "mot_de_passe": MOT_DE_PASSE},
    )
    assert reponse.status_code == 201, reponse.text
    return client
