"""Le squelette repond, et il repond juste."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_la_sonde_repond():
    r = client.get("/api/sante")
    assert r.status_code == 200
    assert r.json()["statut"] == "ok"


def test_le_mode_demo_est_desactive_par_defaut():
    """Un package client ne doit jamais partir en lecture seule par accident."""
    r = client.get("/api/contexte")
    assert r.status_code == 200
    assert r.json()["mode_demo"] is False
