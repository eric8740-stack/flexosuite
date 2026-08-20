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
