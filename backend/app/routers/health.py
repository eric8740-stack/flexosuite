"""Sonde de sante - le seul endpoint ouvert."""
from fastapi import APIRouter

router = APIRouter(tags=["sante"])


@router.get("/sante")
def sante() -> dict:
    return {"statut": "ok", "application": "FlexoSuite"}
