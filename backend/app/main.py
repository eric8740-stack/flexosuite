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

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session as SessionSQL

from app import erreurs
from app.config import CORS_ORIGINES, DEMO_MODE, STATIC_DIR
from app.database import get_db
from app.dependances import METHODES_ECRITURE, installation_faite, utilisateur_courant
from app.models import ParametresCouts, Utilisateur
from app.routers import auth, health, installation
from app.schemas.noyau import Contexte, UtilisateurPublic

app = FastAPI(title="FlexoSuite", version="0.2.0")

# Toute erreur sort au format du contrat : {"code", "detail"}.
erreurs.brancher(app)

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


@app.middleware("http")
async def controle_origine(requete: Request, suivant):
    """Deuxieme serrure contre la falsification de requete.

    `SameSite=Strict` couvre deja l'essentiel. Ce controle tient si un
    navigateur ancien ou une extension traite `SameSite` avec largesse.

    Deux choix explicites :

    - **Les lectures ne sont pas concernees** : elles ne modifient rien.
    - **Une requete SANS en-tete `Origin` passe.** Tout navigateur en envoie un
      sur une methode d'ecriture, y compris pour un formulaire cross-site : une
      requete sans `Origin` ne vient donc pas d'un navigateur, et sans
      navigateur il n'y a pas de cookie transporte a l'insu de l'utilisateur —
      donc pas de falsification possible. Refuser ici casserait les scripts du
      package et les tests sans rien proteger de plus.

    Les origines acceptees sont celle du service **et** celles du reglage de
    partage d'origine : la meme liste qu'ailleurs, pour qu'il n'y ait pas deux
    endroits ou se tromper.
    """
    if requete.method in METHODES_ECRITURE:
        origine = requete.headers.get("origin")
        if origine and origine not in _origines_acceptees(requete):
            erreur = erreurs.origine_refusee()
            return JSONResponse(
                status_code=erreur.status_code,
                content={"code": erreur.code, "detail": erreur.detail},
            )
    return await suivant(requete)


def _origines_acceptees(requete: Request) -> set[str]:
    base = requete.base_url
    return {f"{base.scheme}://{base.netloc}", *CORS_ORIGINES}


app.include_router(health.router, prefix="/api")
app.include_router(installation.router, prefix="/api")
app.include_router(auth.router, prefix="/api")


@app.get("/api/contexte", response_model=Contexte)
def contexte(
    db: SessionSQL = Depends(get_db),
    utilisateur: Utilisateur | None = Depends(utilisateur_courant),
) -> Contexte:
    """Ce que le front doit savoir avant d'afficher quoi que ce soit.

    Toujours accessible **sans session** : c'est lui qui dit s'il en faut une.
    """
    parametres = db.execute(select(ParametresCouts).limit(1)).scalar_one_or_none()
    return Contexte(
        mode_demo=DEMO_MODE,
        installation_faite=installation_faite(db),
        calibration_faite=bool(parametres and parametres.calibration_faite),
        utilisateur=(
            UtilisateurPublic(identifiant=utilisateur.identifiant, role=utilisateur.role)
            if utilisateur
            else None
        ),
    )


# --- Front exporte, monte EN DERNIER -----------------------------------------
# L'ordre compte : monte en premier, `/` capterait aussi les routes d'API.
if STATIC_DIR and Path(STATIC_DIR).is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="web")
