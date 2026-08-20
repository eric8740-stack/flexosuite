# -*- coding: utf-8 -*-
"""Le format d'erreur du contrat : `{"code": ..., "detail": ...}`.

Deux champs, deux publics — c'est ecrit dans `docs/CONTRAT-API.md` et ce module
en est l'application :

- `code` s'adresse a la MACHINE. Stable, il ne change jamais sans passer par le
  journal des changements du contrat.
- `detail` s'adresse a l'HUMAIN. Une phrase en francais, affichable telle quelle
  a un deviseur, reformulable a tout moment.

Le front aiguille sur `code`, jamais sur `detail` — un aiguillage bati sur un
texte casse a la premiere relecture, et il casse **en silence**.
"""
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as HTTPExceptionStarlette

# 422 en clair : la constante de Starlette a change de nom entre deux versions
# (`..._UNPROCESSABLE_ENTITY` -> `..._UNPROCESSABLE_CONTENT`) et emet une alerte
# de depreciation. Le nombre, lui, est fige par le contrat.
HTTP_422 = 422

# Les codes de la v1 du contrat. Ils sont ici pour qu'une faute de frappe se
# voie a l'import, pas en production.
SESSION_ABSENTE = "session_absente"
IDENTIFIANTS_INVALIDES = "identifiants_invalides"
INSTALLATION_REQUISE = "installation_requise"
INSTALLATION_DEJA_FAITE = "installation_deja_faite"
CALIBRATION_REQUISE = "calibration_requise"
MODE_DEMO_LECTURE_SEULE = "mode_demo_lecture_seule"
ORIGINE_REFUSEE = "origine_refusee"
INTROUVABLE = "introuvable"
PAYLOAD_INVALIDE = "payload_invalide"
REGLE_METIER = "regle_metier"


class ErreurApi(HTTPException):
    """Une erreur qui porte son code de contrat."""

    def __init__(self, statut: int, code: str, detail: str) -> None:
        super().__init__(status_code=statut, detail=detail)
        self.code = code


def session_absente() -> ErreurApi:
    return ErreurApi(
        status.HTTP_401_UNAUTHORIZED,
        SESSION_ABSENTE,
        "Votre session a expire ou n'existe pas. Reconnectez-vous.",
    )


def identifiants_invalides() -> ErreurApi:
    # Message VOLONTAIREMENT indifferencie : dire lequel des deux est faux
    # transforme le formulaire en verificateur d'identifiants.
    return ErreurApi(
        status.HTTP_401_UNAUTHORIZED,
        IDENTIFIANTS_INVALIDES,
        "Identifiant ou mot de passe incorrect.",
    )


def installation_requise() -> ErreurApi:
    return ErreurApi(
        status.HTTP_409_CONFLICT,
        INSTALLATION_REQUISE,
        "Aucun compte n'existe encore : commencez par l'installation.",
    )


def installation_deja_faite() -> ErreurApi:
    return ErreurApi(
        status.HTTP_409_CONFLICT,
        INSTALLATION_DEJA_FAITE,
        "L'installation a deja ete faite. Connectez-vous.",
    )


def mode_demo_lecture_seule() -> ErreurApi:
    return ErreurApi(
        status.HTTP_403_FORBIDDEN,
        MODE_DEMO_LECTURE_SEULE,
        "Cette demonstration est en lecture seule : aucune modification n'est enregistree.",
    )


def origine_refusee() -> ErreurApi:
    return ErreurApi(
        status.HTTP_403_FORBIDDEN,
        ORIGINE_REFUSEE,
        "Cette modification a ete refusee : elle ne vient pas de l'application.",
    )


def introuvable(quoi: str = "Cet element") -> ErreurApi:
    return ErreurApi(status.HTTP_404_NOT_FOUND, INTROUVABLE, f"{quoi} n'existe pas.")


def regle_metier(detail: str) -> ErreurApi:
    return ErreurApi(status.HTTP_400_BAD_REQUEST, REGLE_METIER, detail)


# --- Branchement sur l'application ------------------------------------------

# Un code de repli par statut : meme une erreur levee par le framework doit
# sortir au format du contrat. Un front qui rencontre une seule reponse d'une
# autre forme doit ecrire un cas particulier — et c'est ce cas particulier qui
# finira par diverger.
_CODES_PAR_STATUT = {
    status.HTTP_400_BAD_REQUEST: REGLE_METIER,
    status.HTTP_401_UNAUTHORIZED: SESSION_ABSENTE,
    status.HTTP_403_FORBIDDEN: ORIGINE_REFUSEE,
    status.HTTP_404_NOT_FOUND: INTROUVABLE,
    HTTP_422: PAYLOAD_INVALIDE,
}


async def _http(requete: Request, exc: HTTPException) -> JSONResponse:  # noqa: ARG001
    code = getattr(exc, "code", None) or _CODES_PAR_STATUT.get(exc.status_code, REGLE_METIER)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "detail": str(exc.detail)},
        headers=getattr(exc, "headers", None),
    )


async def _validation(requete: Request, exc: RequestValidationError) -> JSONResponse:  # noqa: ARG001
    champs = ", ".join(
        ".".join(str(p) for p in e.get("loc", ()) if p not in ("body", "query"))
        for e in exc.errors()
    )
    return JSONResponse(
        status_code=HTTP_422,
        content={
            "code": PAYLOAD_INVALIDE,
            "detail": f"Champs invalides : {champs}." if champs else "Donnees invalides.",
        },
    )


def brancher(application) -> None:
    """A appeler une fois, sur l'application FastAPI.

    ⚠️ Le gestionnaire se branche sur l'exception de **Starlette**, pas sur
    celle de FastAPI. Une route inconnue leve la premiere, dont la seconde
    herite : s'inscrire sur la classe fille laissait le 404 « route inconnue »
    sortir au format par defaut, `{"detail": ...}` sans `code`. Une seule
    reponse d'une autre forme oblige le front a ecrire un cas particulier.
    """
    application.add_exception_handler(HTTPExceptionStarlette, _http)
    application.add_exception_handler(HTTPException, _http)
    application.add_exception_handler(RequestValidationError, _validation)
