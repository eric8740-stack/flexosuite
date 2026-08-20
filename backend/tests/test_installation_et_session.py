# -*- coding: utf-8 -*-
"""Installation, connexion, session — le chemin d'entree de l'application.

Ce que ces tests protegent, dans l'ordre d'importance :

1. **L'assistant d'installation ne se rejoue pas.** Rejouable, il serait une
   porte d'entree sur une installation en service.
2. **La revocation est cote serveur.** Effacer le cookie sur un poste ne protege
   rien si le jeton reste valide.
3. **L'application part a ZERO TARIF.** `calibration_faite` doit etre faux au
   sortir de l'installation, sinon le front afficherait des prix a zero — et un
   prix faux est pire qu'une absence de prix.
"""
from datetime import timedelta

from sqlalchemy import select

from app.database import SessionLocale
from app.models import ParametresCouts, SessionUtilisateur, maintenant
from app.services.sessions import NOM_COOKIE
from tests.conftest import IDENTIFIANT, MOT_DE_PASSE


# --- Contexte ---------------------------------------------------------------


def test_contexte_est_lisible_sans_session(client):
    """C'est lui qui dit s'il faut une session : l'exiger serait circulaire."""
    r = client.get("/api/contexte")
    assert r.status_code == 200
    assert r.json() == {
        "mode_demo": False,
        "installation_faite": False,
        "calibration_faite": False,
        "utilisateur": None,
    }


def test_contexte_apres_installation(client_installe):
    corps = client_installe.get("/api/contexte").json()
    assert corps["installation_faite"] is True
    assert corps["utilisateur"] == {"identifiant": IDENTIFIANT, "role": "administrateur"}
    # Le point qui compte : l'installation ne calibre rien.
    assert corps["calibration_faite"] is False


def test_l_installation_ne_pose_aucun_tarif(client_installe):
    """Un seul chiffre est livre, et ce n'est pas un tarif : la marge."""
    with SessionLocale() as db:
        p = db.execute(select(ParametresCouts)).scalar_one()
        assert p.marge_standard_pct is not None
        assert p.cout_exploitation_machine_eur_h is None
        assert p.cliche_prix_couleur_eur is None
        assert p.calibration_faite is False


# --- Installation -----------------------------------------------------------


def test_l_installation_ouvre_la_session_dans_la_foulee(client_installe):
    assert client_installe.get("/api/auth/moi").status_code == 200


def test_l_installation_ne_se_rejoue_pas(client_installe):
    r = client_installe.post(
        "/api/installation",
        json={"identifiant": "autre", "mot_de_passe": "un-autre-mot-de-passe"},
    )
    assert r.status_code == 409
    assert r.json()["code"] == "installation_deja_faite"


def test_un_mot_de_passe_trop_court_est_refuse(client):
    r = client.post("/api/installation", json={"identifiant": "a", "mot_de_passe": "court"})
    assert r.status_code == 422
    assert r.json()["code"] == "payload_invalide"


# --- Connexion --------------------------------------------------------------


def test_connexion_impossible_avant_installation(client):
    r = client.post(
        "/api/auth/connexion",
        json={"identifiant": IDENTIFIANT, "mot_de_passe": MOT_DE_PASSE},
    )
    assert r.status_code == 409
    assert r.json()["code"] == "installation_requise"


def test_connexion_et_reconnexion(client_installe):
    client_installe.post("/api/auth/deconnexion")
    r = client_installe.post(
        "/api/auth/connexion",
        json={"identifiant": IDENTIFIANT, "mot_de_passe": MOT_DE_PASSE},
    )
    assert r.status_code == 200
    assert client_installe.get("/api/auth/moi").json()["identifiant"] == IDENTIFIANT


def test_le_message_ne_dit_pas_lequel_est_faux(client_installe):
    """Un message different selon le cas transformerait le formulaire en
    verificateur d'identifiants."""
    client_installe.post("/api/auth/deconnexion")
    mauvais_identifiant = client_installe.post(
        "/api/auth/connexion",
        json={"identifiant": "inconnu", "mot_de_passe": MOT_DE_PASSE},
    )
    mauvais_mot_de_passe = client_installe.post(
        "/api/auth/connexion",
        json={"identifiant": IDENTIFIANT, "mot_de_passe": "mauvais-mot-de-passe"},
    )
    assert mauvais_identifiant.status_code == mauvais_mot_de_passe.status_code == 401
    assert mauvais_identifiant.json() == mauvais_mot_de_passe.json()
    assert mauvais_identifiant.json()["code"] == "identifiants_invalides"


# --- Session ----------------------------------------------------------------


def test_sans_session_c_est_401(client_installe):
    client_installe.cookies.clear()
    r = client_installe.get("/api/auth/moi")
    assert r.status_code == 401
    assert r.json()["code"] == "session_absente"


def test_le_jeton_n_est_pas_stocke_en_clair(client_installe):
    """Une lecture de la base ne doit pas permettre de se faire passer pour
    quelqu'un."""
    jeton = client_installe.cookies[NOM_COOKIE]
    with SessionLocale() as db:
        stocke = db.execute(select(SessionUtilisateur.jeton_hache)).scalar_one()
    assert jeton
    assert stocke != jeton


def test_la_deconnexion_revoque_en_base(client_installe):
    """Le point du contrat : la session est invalidee cote SERVEUR. On remet le
    cookie a la main pour le prouver — l'effacer suffirait a faire passer un
    test qui ne verifie que le navigateur."""
    jeton = client_installe.cookies[NOM_COOKIE]
    assert client_installe.post("/api/auth/deconnexion").status_code == 204

    with SessionLocale() as db:
        assert db.execute(select(SessionUtilisateur.revoquee_le)).scalar_one() is not None

    client_installe.cookies.set(NOM_COOKIE, jeton)
    assert client_installe.get("/api/auth/moi").status_code == 401


def test_la_deconnexion_reussit_meme_sans_session(client):
    """Renvoyer 401 a quelqu'un qui veut partir n'aurait aucun sens."""
    assert client.post("/api/auth/deconnexion").status_code == 204


def test_une_session_expiree_ne_vaut_plus_rien(client_installe):
    """L'expiration est ABSOLUE : pas de prolongation glissante. Une session
    oubliee sur un poste d'atelier finit par expirer, quoi qu'il arrive."""
    with SessionLocale() as db:
        session = db.execute(select(SessionUtilisateur)).scalar_one()
        session.expire_le = maintenant() - timedelta(seconds=1)
        db.commit()
    r = client_installe.get("/api/auth/moi")
    assert r.status_code == 401
    assert r.json()["code"] == "session_absente"


def test_les_attributs_du_cookie_sont_ceux_du_contrat(client):
    r = client.post(
        "/api/installation",
        json={"identifiant": IDENTIFIANT, "mot_de_passe": MOT_DE_PASSE},
    )
    brut = r.headers["set-cookie"].lower()
    assert brut.startswith(f"{NOM_COOKIE}=")
    assert "httponly" in brut          # le front ne lit jamais le jeton
    assert "samesite=strict" in brut   # le port n'entre pas dans same-site
    assert "path=/" in brut            # un seul port sert la page et l'API
