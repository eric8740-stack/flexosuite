# -*- coding: utf-8 -*-
"""Le script de secours du client — teste sur son COMPORTEMENT REEL.

Pourquoi ce script existe : le mot de passe n'est stocke que HACHE. Le jour ou
un imprimeur le perd, `reinitialiser-mot-de-passe.bat` est son seul recours.

> Ce fichier a remplace, au lot 2, le test provisoire qui verifiait seulement
> que le module echouait bruyamment tant que l'authentification n'existait pas.
> Il verifie maintenant ce qui compte : le mot de passe est bien remplace,
> l'ancien ne fonctionne plus, et **les sessions ouvertes sont revoquees**.

⚠️ CE QUE CES TESTS NE PROUVENT PAS. Les cas par sous-processus lancent
`sys.executable`, c'est-a-dire le Python de l'environnement de test — pas le
Python EMBARQUE du package. Ils ne disent rien du fichier `._pth` ni du chemin
d'import chez le client. **La preuve de packaging est ailleurs** :
`deploy/windows/build-package.ps1` § 6 bis importe `app.main` et
`scripts.reinitialiser_admin` avec le Python embarque, depuis le dossier backend
assemble — exactement comme le feront les scripts double-clic.
"""
import subprocess
import sys
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocale
from app.models import SessionUtilisateur
from scripts.reinitialiser_admin import main
from tests.conftest import IDENTIFIANT, MOT_DE_PASSE

RACINE_BACKEND = Path(__file__).resolve().parent.parent
NOUVEAU = "nouveau-mot-de-passe"


def _saisie(*reponses: str):
    """Remplace la saisie clavier. Le mot de passe n'est jamais un argument de
    ligne de commande : une ligne de commande se retrouve dans l'historique."""
    restant = list(reponses)
    return lambda _invite: restant.pop(0)


def _lancer_par_moins_m() -> subprocess.CompletedProcess:
    """Par `-m`, depuis le dossier backend — la forme qu'emploie le .bat.
    Appeler `main()` en direct ne prouverait pas qu'il est atteignable."""
    return subprocess.run(
        [sys.executable, "-m", "scripts.reinitialiser_admin"],
        cwd=RACINE_BACKEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        input="",
    )


# --- Comportement reel ------------------------------------------------------


def test_le_mot_de_passe_est_bien_remplace(client_installe):
    assert main(lire=_saisie(NOUVEAU, NOUVEAU)) == 0

    client_installe.cookies.clear()
    ancien = client_installe.post(
        "/api/auth/connexion",
        json={"identifiant": IDENTIFIANT, "mot_de_passe": MOT_DE_PASSE},
    )
    assert ancien.status_code == 401, "L'ancien mot de passe doit cesser de fonctionner."

    nouveau = client_installe.post(
        "/api/auth/connexion",
        json={"identifiant": IDENTIFIANT, "mot_de_passe": NOUVEAU},
    )
    assert nouveau.status_code == 200


def test_les_sessions_ouvertes_sont_revoquees(client_installe):
    """Sans cela, le poste laisse ouvert dans l'atelier continuerait a
    fonctionner : le mot de passe changerait sans rien fermer."""
    assert client_installe.get("/api/auth/moi").status_code == 200

    assert main(lire=_saisie(NOUVEAU, NOUVEAU)) == 0

    assert client_installe.get("/api/auth/moi").status_code == 401
    with SessionLocale() as db:
        assert db.execute(select(SessionUtilisateur.revoquee_le)).scalar_one() is not None


def test_deux_saisies_differentes_ne_changent_rien(client_installe):
    assert main(lire=_saisie(NOUVEAU, "pas-la-meme-chose")) == 1
    assert client_installe.get("/api/auth/moi").status_code == 200


def test_un_mot_de_passe_trop_court_est_refuse(client_installe):
    assert main(lire=_saisie("court", "court")) == 1
    assert client_installe.get("/api/auth/moi").status_code == 200


# --- Echecs bruyants --------------------------------------------------------


def test_sans_compte_il_echoue_et_dit_quoi_faire(client):
    """Un succes silencieux ferait croire au client que son mot de passe est
    reinitialise alors qu'il resterait bloque."""
    resultat = _lancer_par_moins_m()
    assert resultat.returncode != 0
    assert resultat.stdout.strip() == "", "Pas de demi-message laissant croire a un debut de travail."
    assert "installation" in resultat.stderr.lower()


def test_le_module_est_atteignable_par_moins_m(client):
    """Ce que ce test N'ATTRAPE PAS : le defaut du 20/08/2026, ou le module
    etait bien livre mais introuvable dans le Python EMBARQUE. Ce cas se
    verifie a l'assemblage — build-package.ps1 § 6 bis."""
    assert "ModuleNotFoundError" not in _lancer_par_moins_m().stderr
