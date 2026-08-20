# -*- coding: utf-8 -*-
"""Le MODULE de reinitialisation : atteignable par `-m`, et bruyant en echec.

⚠️ CE QUE CE TEST NE PROUVE PAS. Il lance `sys.executable`, c'est-a-dire le
Python de l'environnement de test — pas le Python EMBARQUE du package. Il ne
dit donc rien du fichier `._pth`, ni du chemin d'import chez le client.

**La preuve de packaging est ailleurs, et elle est correcte** :
`deploy/windows/build-package.ps1` § 6 bis importe `app.main` et
`scripts.reinitialiser_admin` avec le Python embarque, depuis le dossier
backend assemble — exactement comme le feront les scripts double-clic.

Ce test-ci verifie ce qui est de son ressort : que le module existe, qu'il est
atteignable par `-m`, et qu'il echoue BRUYAMMENT tant qu'il n'est pas
implemente — jamais en silence.

Pourquoi un test pour un script qui ne fait rien : le mot de passe
administrateur n'est stocke que HACHE. Le jour ou un imprimeur le perd, ce
script est son seul recours. S'il sortait en code 0 sans rien faire, le client
croirait son mot de passe reinitialise et resterait bloque — avec, en prime,
l'idee que l'outil est cense marcher.

Un echec bruyant est une promesse tenue : « ce n'est pas encore la ». Un succes
silencieux est un mensonge.

⚠️ Ce test change de nature au lot 2 : quand l'authentification arrive, il doit
etre remplace par un test du comportement REEL (le mot de passe est bien
remplace, et l'ancien ne fonctionne plus). Ne pas le supprimer sans ecrire son
successeur.
"""
import subprocess
import sys
from pathlib import Path

RACINE_BACKEND = Path(__file__).resolve().parent.parent


def _lancer_le_script() -> subprocess.CompletedProcess:
    """Par `-m`, depuis le dossier backend — la forme qu'emploie le script
    double-clic. Appeler `main()` en direct ne prouverait pas qu'il est
    atteignable.

    ⚠️ `sys.executable` est le Python de l'environnement de TEST, pas celui du
    package : voir l'avertissement en tete de module."""
    return subprocess.run(
        [sys.executable, "-m", "scripts.reinitialiser_admin"],
        cwd=RACINE_BACKEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_le_module_est_atteignable_par_moins_m():
    """Le module doit exister et s'invoquer par `-m` depuis le dossier backend :
    c'est la forme qu'emploie le script double-clic.

    Ce que ce test N'ATTRAPE PAS : le defaut du 20/08/2026, ou le module etait
    bien livre mais introuvable dans le Python EMBARQUE (son `._pth` n'exposait
    pas le dossier backend). Ce cas-la se verifie a l'assemblage —
    build-package.ps1 § 6 bis."""
    r = _lancer_le_script()
    assert "ModuleNotFoundError" not in r.stderr, (
        "Le module n'est pas atteignable par `-m` depuis le dossier backend."
    )


def test_il_echoue_avec_un_code_non_nul():
    """Le script double-clic teste le code de retour : un 0 le ferait annoncer
    une reussite a un technicien qui compte dessus."""
    assert _lancer_le_script().returncode != 0


def test_il_dit_pourquoi_et_sur_la_sortie_d_erreur():
    r = _lancer_le_script()
    assert r.stderr.strip(), "Un echec muet ne renseigne personne."
    assert "lot 2" in r.stderr, (
        "Le message doit dire QUAND ce sera disponible, pas seulement que ca "
        "ne l'est pas."
    )


def test_il_n_ecrit_rien_sur_la_sortie_standard():
    """Rien sur la sortie standard : pas de demi-message qui laisserait croire
    qu'une partie du travail a ete faite."""
    assert _lancer_le_script().stdout.strip() == ""
