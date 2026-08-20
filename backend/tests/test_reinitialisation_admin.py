# -*- coding: utf-8 -*-
"""Le script de reinitialisation doit echouer BRUYAMMENT tant qu'il n'est pas
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
    """On lance le script comme le fait le .bat : par `-m`, depuis le dossier
    backend. Appeler `main()` en direct ne prouverait pas qu'il est atteignable."""
    return subprocess.run(
        [sys.executable, "-m", "scripts.reinitialiser_admin"],
        cwd=RACINE_BACKEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_le_script_est_atteignable_par_le_meme_chemin_que_le_bat():
    """Le 20/08/2026, le script echouait chez le client sur un ModuleNotFound
    alors qu'il etait bien livre : le Python embarque n'exposait pas le dossier
    backend. L'echec etait bruyant, mais pour la mauvaise raison — et un mauvais
    motif d'echec envoie le technicien chercher au mauvais endroit."""
    r = _lancer_le_script()
    assert "ModuleNotFoundError" not in r.stderr, (
        "Le script n'est pas importable par `-m` : verifier le chemin declare "
        "dans le fichier ._pth du Python embarque (build-package.ps1)."
    )


def test_il_echoue_avec_un_code_non_nul():
    """Le .bat teste le code de retour : un 0 le ferait annoncer une reussite."""
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
