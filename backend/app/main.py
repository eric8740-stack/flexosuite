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

from app.config import DEMO_MODE, STATIC_DIR
from app.routers import health

app = FastAPI(title="FlexoSuite", version="0.1.0")

# CORS : utile uniquement en developpement (deux ports). En production
# mono-port, la page et l'API ont la meme origine et rien ne passe par ici.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
