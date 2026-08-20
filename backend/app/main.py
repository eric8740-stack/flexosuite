"""Point d'entree FastAPI.

MONO-PORT : ce processus sert l'API **et** le front exporte. C'est ce qui rend
la livraison possible - un seul service a demarrer chez le client, aucun serveur
web a configurer.

En developpement, `FLEXO_STATIC_DIR` n'est pas defini : le front tourne sur son
propre port et parle a l'API via `NEXT_PUBLIC_API_URL`. Au build du package,
cette variable est RETIREE cote front (base d'API relative) et le backend monte
l'export statique ici. Meme code, deux modes.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINES, DEMO_MODE, STATIC_DIR
from app.routers import health

app = FastAPI(title="FlexoSuite", version="0.1.0")

# --- Partage d'origine : DEVELOPPEMENT UNIQUEMENT ----------------------------
# Le middleware n'est monte QUE si des origines sont explicitement listees. Les
# deux livrables tournent en mono-port : la page et l'API ont la meme origine,
# et le partage d'origine n'y sert a rien. En laisser un actif « au cas ou »
# reviendrait a livrer chez le client une autorisation dont il n'a pas besoin.
#
# Origines exactes, jamais `*` : l'application transporte une session par
# cookie, et `*` avec des cookies est refuse par la specification. La garde est
# dans app/config.py, au demarrage.
if CORS_ORIGINES:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINES,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

app.include_router(health.router, prefix="/api")


@app.get("/api/contexte")
def contexte() -> dict:
    """Ce que le front doit savoir avant d'afficher quoi que ce soit."""
    return {"mode_demo": DEMO_MODE}


# --- Front exporte, monte EN DERNIER -----------------------------------------
# L'ordre compte : monte en premier, `/` capterait aussi les routes d'API.
if STATIC_DIR and Path(STATIC_DIR).is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="web")
