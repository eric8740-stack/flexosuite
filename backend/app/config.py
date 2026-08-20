r"""Configuration - lue dans l'environnement, jamais en dur.

Principe de livraison locale : le CODE et les DONNEES sont separes. En
production Windows, `_env.bat` pose DATABASE_URL vers %ProgramData%\FlexoSuite
et le code ne sait rien de cet emplacement. En developpement, on retombe sur un
fichier SQLite local.
"""
import os
from pathlib import Path

RACINE_BACKEND = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{RACINE_BACKEND / 'dev.db'}")

# Dossier du front exporte, servi par le backend (mono-port). Absent en
# developpement : le front tourne alors sur son propre port.
STATIC_DIR = os.getenv("FLEXO_STATIC_DIR")

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# Mode demo : lecture seule, pour la vitrine publique.
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"

# --- Partage d'origine (CORS) : DEVELOPPEMENT UNIQUEMENT --------------------
#
# Les deux livrables tournent en MONO-PORT : la page et l'API ont la meme
# origine, et aucune requete ne passe par le partage d'origine. Il n'a donc
# rien a faire dans le package Windows ni sur la demo.
#
# Il n'est utile qu'en developpement, quand le front tourne sur son propre
# port. On l'active alors EXPLICITEMENT, en listant les origines exactes :
#
#     CORS_ORIGINES=http://localhost:3000
#
# ⚠️ UN SEUL NOM D'HOTE, le meme que celui employe par le front. `localhost` et
# `127.0.0.1` sont deux hotes DIFFERENTS pour la regle same-site : les melanger
# donne une session qui « ne tient pas », sans le moindre message d'erreur.
# La marche a suivre complete est dans le README, section « Demarrage en
# developpement ».
#
# Vide par defaut = middleware absent. Un defaut permissif serait livre chez le
# client sans que personne ne le remarque.
_origines_brutes = os.getenv("CORS_ORIGINES", "").strip()
CORS_ORIGINES = [o.strip() for o in _origines_brutes.split(",") if o.strip()]

# `*` avec des cookies de session est refuse par la specification, et serait de
# toute facon une porte ouverte. On echoue au demarrage plutot que de laisser
# un reglage dangereux passer inapercu.
if "*" in CORS_ORIGINES:
    raise RuntimeError(
        "CORS_ORIGINES ne peut pas valoir '*' : l'application transporte une "
        "session par cookie. Listez les origines exactes."
    )

# --- Cookie de session ------------------------------------------------------
#
# `Secure` est un REGLAGE, pas une constante : la demo publique est en HTTPS et
# l'exige, le package client tourne en HTTP sur le reseau de l'imprimerie et
# s'en trouverait bloque. Defaut sur : la dérogation est explicite.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "1") != "0"

# Duree de vie d'une session, en heures. Au-dela, il faut se reconnecter.
SESSION_DUREE_H = int(os.getenv("SESSION_DUREE_H", "12"))
