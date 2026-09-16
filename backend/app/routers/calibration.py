# -*- coding: utf-8 -*-
"""L'assistant de calibration — il PROPOSE, il n'enregistre pas.

Le calcul ne touche pas la base : c'est un `PUT` sur les parametres qui decide.
Un assistant qui ecrirait tout seul retirerait a l'imprimeur le seul moment qui
compte ici — celui ou il dit oui.

⚠️ **Cet endpoint n'est PAS soumis a `interdire_ecriture_demo`, et c'est un
choix.** C'est un `POST`, mais il n'ecrit rien : le refuser en mode demo
retirerait a la demonstration publique l'ecran qui montre le mieux ce que fait
l'application, sans rien proteger — il n'y a rien a proteger, aucune ligne n'est
touchee.

**Le jour ou cet endpoint ecrira quoi que ce soit, la garde doit revenir.** Un
test verifie qu'il repond en mode demo ; il tombera si on la remet, et c'est
alors ce commentaire qu'il faudra relire.
"""
from fastapi import APIRouter, Depends

from app.dependances import exiger_session
from app.schemas.parametres import CalibrationTauxMachine, TauxMachinePublic
from app.services import calibration

router = APIRouter(
    prefix="/calibration",
    tags=["calibration"],
    dependencies=[Depends(exiger_session)],
)


@router.post("/taux-machine", response_model=TauxMachinePublic)
def taux_machine(entree: CalibrationTauxMachine) -> TauxMachinePublic:
    """Le taux horaire machine, et son detail ligne par ligne.

    Les champs sont passes un par un plutot que par `model_dump()` : les
    decimaux du contrat se **serialisent en chaine**, et un `model_dump()`
    rendrait donc des `str` la ou la formule attend des `Decimal`. Lus en
    attribut, ce sont bien des `Decimal`.
    """
    resultat = calibration.taux_machine(
        prix_achat_presse_eur=entree.prix_achat_presse_eur,
        duree_amortissement_ans=entree.duree_amortissement_ans,
        heures_productives_par_an=entree.heures_productives_par_an,
        energie_eur_an=entree.energie_eur_an,
        maintenance_eur_an=entree.maintenance_eur_an,
    )
    return TauxMachinePublic.model_validate(resultat)
