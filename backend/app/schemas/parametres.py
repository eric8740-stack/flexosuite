# -*- coding: utf-8 -*-
"""Parametres de couts, calibration et baremes — section 6 du contrat.

Trois schemas portent ici une regle qu'on ne retrouve nulle part ailleurs dans
le projet : **un champ accepte et IGNORE**. `calibration_faite` cote parametres,
`type`, `libelle` et `neutre` cote baremes. Ce ne sont pas des oublis de
validation : ce sont des champs **calcules ou portes par l'URL**, et le front
les renvoie naturellement parce qu'il repose l'objet qu'il vient de lire.

Les refuser obligerait chaque ecran a fabriquer un corps ampute de ce qu'il
vient de recevoir — c'est exactement le genre de detail qu'un front oublie une
fois sur deux, et qui produit un 422 incomprehensible.
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.decimaux import Decimal2, Decimal4

ECRITURE = ConfigDict(extra="forbid")
LECTURE = ConfigDict(from_attributes=True)


class ParametresCoutsPublic(BaseModel):
    """Les dix champs, plus le booleen calcule.

    ⚠️ **Tout est `null` a l'installation, sauf la marge.** L'application se
    livre a ZERO TARIF : livrer les tarifs d'un autre atelier produirait des
    devis faux, et un devis faux se decouvre chez le client.
    """

    model_config = LECTURE

    # En POURCENTAGE. `x (1 + pct/100)` est une marge SUR COUT DE REVIENT, pas
    # un taux de marque : a 30 %, le coefficient vaut 1,30. Un imprimeur qui lit
    # un taux de marque attend 1,4286 et facture 9 % en dessous.
    marge_standard_pct: Decimal2
    cout_exploitation_machine_eur_h: Decimal2 | None
    cout_operateur_eur_h: Decimal2 | None
    marge_confort_roulage_mm: int | None
    cliche_prix_couleur_eur: Decimal2 | None
    outil_base_eur: Decimal2 | None
    outil_par_trace_eur: Decimal2 | None
    surcout_forme_speciale_facteur: Decimal2 | None
    calage_forfait_eur: Decimal2 | None
    # QUATRE decimales, comme `matiere.prix_m2_eur` : c'est un prix au m2, et la
    # troisieme decimale pese sur un tirage de plusieurs milliers de metres.
    finitions_prix_m2_eur: Decimal4 | None
    # CALCULE. Vrai quand les neuf autres champs sont renseignes.
    calibration_faite: bool


class ParametresCoutsModification(BaseModel):
    """`PUT` **partiel** : seuls les champs envoyes sont modifies.

    C'est le seul `PUT` partiel du contrat, et la raison est dans l'usage : on
    enregistre ces valeurs **champ par champ**, au fil de l'assistant de
    calibration. Les referentiels, eux, se saisissent dans un formulaire entier
    et se remplacent en bloc.
    """

    model_config = ECRITURE

    marge_standard_pct: Decimal2 | None = None
    cout_exploitation_machine_eur_h: Decimal2 | None = None
    cout_operateur_eur_h: Decimal2 | None = None
    marge_confort_roulage_mm: int | None = Field(default=None, ge=0)
    cliche_prix_couleur_eur: Decimal2 | None = None
    outil_base_eur: Decimal2 | None = None
    outil_par_trace_eur: Decimal2 | None = None
    surcout_forme_speciale_facteur: Decimal2 | None = None
    calage_forfait_eur: Decimal2 | None = None
    finitions_prix_m2_eur: Decimal4 | None = None
    # Accepte et IGNORE : il est calcule. Le refuser casserait le geste naturel
    # « je relis l'objet, je modifie un champ, je repose l'objet ».
    calibration_faite: bool | None = None

    @model_validator(mode="after")
    def _la_marge_ne_se_vide_pas(self) -> "ParametresCoutsModification":
        """La marge est le SEUL champ chiffre livre, et elle n'a pas de repli.

        Un devis calcule sans marge se vendrait au prix de revient. Ne pas
        l'envoyer est permis (le `PUT` est partiel) ; l'envoyer vide, non.
        """
        if "marge_standard_pct" in self.model_fields_set and self.marge_standard_pct is None:
            raise ValueError("marge_standard_pct ne peut pas etre vide")
        return self

    def champs_modifies(self) -> dict[str, Any]:
        """Les seuls champs reellement envoyes, `calibration_faite` retire."""
        donnees = self.model_dump(exclude_unset=True)
        donnees.pop("calibration_faite", None)
        return donnees


class CalibrationTauxMachine(BaseModel):
    """Ce que l'imprimeur connait — **jamais un tarif a recopier**."""

    model_config = ECRITURE

    prix_achat_presse_eur: Decimal2 = Field(gt=0)
    # Les deux diviseurs de la formule : strictement positifs, sinon 422. La
    # division ne se protege pas plus loin, elle se protege ici.
    duree_amortissement_ans: int = Field(gt=0)
    heures_productives_par_an: int = Field(gt=0)
    energie_eur_an: Decimal2 = Field(ge=0)
    maintenance_eur_an: Decimal2 = Field(ge=0)


class LigneTaux(BaseModel):
    model_config = LECTURE

    libelle: str
    montant_eur_h: Decimal2


class TauxMachinePublic(BaseModel):
    """Le taux **et son explication** : un chiffre qu'on ne sait pas justifier
    ne sera pas adopte."""

    model_config = LECTURE

    taux_eur_h: Decimal2
    detail: list[LigneTaux]


class BaremePublic(BaseModel):
    """Pas d'`id` : le `type` est la cle, et c'est lui qui est dans l'URL."""

    model_config = LECTURE

    type: str
    libelle: str
    # CALCULE a partir de `donnees` — cf. `app/models/baremes.py`.
    neutre: bool
    # Vide = TOUTES les machines. Contre-intuitif, et c'est le sens du contrat.
    machines_ids: list[int]
    donnees: dict
    actif: bool


class BaremeEcriture(BaseModel):
    """Calibrer un bareme : ses machines, ses donnees, son activation.

    `type`, `libelle` et `neutre` sont **acceptes et ignores** — le premier est
    porte par l'URL, le deuxieme appartient au type, le troisieme est calcule.
    Le front repose l'objet qu'il a lu sans avoir a l'amputer.
    """

    model_config = ECRITURE

    machines_ids: list[int] = Field(default_factory=list)
    donnees: dict
    actif: bool = True

    type: str | None = None
    libelle: str | None = None
    neutre: bool | None = None
