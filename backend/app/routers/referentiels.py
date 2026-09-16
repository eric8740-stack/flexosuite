# -*- coding: utf-8 -*-
"""Un seul routeur CRUD, instancie SIX fois — section 5 du contrat.

Le contrat dit « meme forme pour tous » ; six fichiers presque identiques
finiraient par ne plus l'etre. La pagination corrigee dans cinq routeurs sur six
est un defaut qu'aucune relecture n'attrape, et qui se decouvre chez le client
le jour ou un referentiel depasse un ecran.

Ce qui est generique : la pagination, l'enveloppe de liste, les quatre codes
d'erreur, les gardes. Ce qui reste propre a chaque ressource est **declare**
dans une `Ressource` et nulle part ailleurs : ses cles uniques, ses cles
etrangeres, sa designation en francais.

**Les gardes sont posees sur le ROUTEUR, pas sur chaque endpoint**, et dans
l'ordre voulu : session (401) puis mode demo (403). Une garde recopiee cinq fois
sur six est un trou, et un trou ne se voit pas a la relecture.
"""
from dataclasses import dataclass
from typing import Generic, TypeVar

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SessionSQL

from app import erreurs
from app.database import get_db
from app.dependances import exiger_session, interdire_ecriture_demo
from app.models import Client, Cylindre, Machine, Matiere, Option, Outil
from app.schemas import referentiels as sch
from app.services.referentiels import est_reference

# Les bornes du contrat. Au-dela de la taille maxi : 422 `payload_invalide`.
PAGE_PAR_DEFAUT = 1
TAILLE_PAR_DEFAUT = 25
TAILLE_MAXI = 200

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """L'enveloppe de liste, la MEME partout — devis compris, au lot 2c.

    Une seule forme de liste a ecrire cote front, et un referentiel qui grossit
    ne casse rien le jour ou il depasse un ecran.
    """

    elements: list[T]
    total: int


@dataclass(frozen=True)
class CleUnique:
    colonnes: tuple[str, ...]
    # Ce que l'utilisateur lira : « un enregistrement existe deja avec ce nom ».
    libelle: str


@dataclass(frozen=True)
class CleEtrangere:
    champ: str
    modele: type


@dataclass(frozen=True)
class Ressource:
    chemin: str
    etiquette: str
    modele: type
    ecriture: type[BaseModel]
    # Le schema du `PUT` : memes champs, mais TOUS obligatoires. Cf. constat 1
    # de l'audit du 16/09/2026 — « remplacement complet » n'etait vrai que pour
    # les champs sans valeur par defaut.
    remplacement: type[BaseModel]
    public: type[BaseModel]
    # « cette machine », « cet outil » — le genre francais ne se devine pas.
    designation: str
    cles_uniques: tuple[CleUnique, ...]
    cles_etrangeres: tuple[CleEtrangere, ...] = ()


def _exiger(db: SessionSQL, r: Ressource, id_element: int):
    element = db.get(r.modele, id_element)
    if element is None:
        raise erreurs.introuvable(r.designation[0].upper() + r.designation[1:])
    return element


def _valider_cles_etrangeres(db: SessionSQL, r: Ressource, donnees: dict) -> None:
    """Un identifiant qui ne designe rien est un CHAMP fautif, donc un 422.

    Le 404 serait ambigu : le contrat s'en sert deja pour « cet endpoint n'est
    pas encore livre ». Un front qui recoit 404 sur un POST ne saurait pas s'il
    doit surligner un champ ou renoncer a l'ecran.
    """
    for cle in r.cles_etrangeres:
        valeur = donnees.get(cle.champ)
        if valeur is None:
            continue
        if db.get(cle.modele, valeur) is None:
            raise erreurs.payload_invalide(
                f"{cle.champ} (aucun element ne porte cet identifiant)"
            )


def _cle_en_conflit(
    db: SessionSQL, r: Ressource, donnees: dict, sauf_id: int | None
) -> CleUnique | None:
    for cle in r.cles_uniques:
        conditions = [getattr(r.modele, c) == donnees[c] for c in cle.colonnes]
        requete = select(r.modele.id).where(*conditions)
        if sauf_id is not None:
            requete = requete.where(r.modele.id != sauf_id)
        if db.execute(requete.limit(1)).first() is not None:
            return cle
    return None


def _commettre(
    db: SessionSQL, r: Ressource, donnees: dict, sauf_id: int | None = None
) -> None:
    """C'est la BASE qui tranche l'unicite, pas une lecture prealable.

    Verifier « ce nom existe-t-il ? » puis inserer laisse une fenetre entre les
    deux. La contrainte SQL, elle, ne la laisse pas. La relecture qui suit ne
    sert qu'a NOMMER le champ fautif dans un message lisible.
    """
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        cle = _cle_en_conflit(db, r, donnees, sauf_id)
        if cle is None:
            # La base a refuse pour une raison que nous n'avons pas su nommer.
            # Inventer « deja existant » ici mentirait sur la cause : mieux vaut
            # une erreur franche qu'un diagnostic faux.
            raise
        raise erreurs.deja_existant(cle.libelle) from exc


def creer_routeur(r: Ressource) -> APIRouter:
    routeur = APIRouter(
        prefix=r.chemin,
        tags=[r.etiquette],
        # ORDRE VOULU, et il compte : session d'abord (401, le front redirige
        # sans perdre la saisie), mode demo ensuite (403). `interdire_ecriture_demo`
        # ne mord que sur les methodes d'ecriture : pose ici, aucune ne peut
        # l'oublier.
        dependencies=[Depends(exiger_session), Depends(interdire_ecriture_demo)],
    )
    page_modele = Page[r.public]

    @routeur.get("", response_model=page_modele)
    def lister(
        page: int = Query(PAGE_PAR_DEFAUT, ge=1),
        taille: int = Query(TAILLE_PAR_DEFAUT, ge=1, le=TAILLE_MAXI),
        db: SessionSQL = Depends(get_db),
    ):
        """Les elements desactives sont LISTES comme les autres.

        Pas de filtre cache : c'est l'optimisation (lot 2c) qui ignorera
        `actif = false`. Une liste qui masque discretement des lignes fait
        chercher pendant une demi-heure une machine qui est pourtant la.
        """
        total = db.execute(select(func.count()).select_from(r.modele)).scalar_one()
        # `order_by(id)` n'est pas cosmetique : sans ordre explicite, SQLite est
        # libre de rendre les lignes dans un ordre different d'une requete a
        # l'autre, et une pagination sautera ou repetera des elements.
        elements = (
            db.execute(
                select(r.modele)
                .order_by(r.modele.id)
                .offset((page - 1) * taille)
                .limit(taille)
            )
            .scalars()
            .all()
        )
        return page_modele(
            elements=[r.public.model_validate(e) for e in elements], total=total
        )

    @routeur.get("/{id_element}", response_model=r.public)
    def obtenir(id_element: int, db: SessionSQL = Depends(get_db)):
        return r.public.model_validate(_exiger(db, r, id_element))

    @routeur.post("", response_model=r.public, status_code=status.HTTP_201_CREATED)
    def creer(entree: r.ecriture, db: SessionSQL = Depends(get_db)):
        donnees = entree.model_dump()
        _valider_cles_etrangeres(db, r, donnees)
        element = r.modele(**donnees)
        db.add(element)
        _commettre(db, r, donnees)
        db.refresh(element)
        return r.public.model_validate(element)

    @routeur.put("/{id_element}", response_model=r.public)
    def remplacer(
        id_element: int, entree: r.remplacement, db: SessionSQL = Depends(get_db)
    ):
        """REMPLACEMENT COMPLET, pas une modification partielle.

        Le `PUT` partiel du contrat est celui des **parametres de couts**
        (section 6), et il l'est parce qu'on y enregistre champ par champ. Un
        referentiel se saisit dans un formulaire entier : accepter un corps
        partiel ferait disparaitre en silence les champs que le front aurait
        oublie de renvoyer.

        ⚠️ Le schema est `r.remplacement` et NON `r.ecriture` : c'est tout le
        correctif du constat 1 de l'audit. Avec le schema de creation, les champs
        porteurs d'un defaut (`actif`, `modules`, `contact`...) n'etaient pas
        exiges — ils etaient **reinitialises en silence**. Un `PUT` qui oubliait
        `actif` reactivait un element desactive.
        """
        element = _exiger(db, r, id_element)
        donnees = entree.model_dump()
        _valider_cles_etrangeres(db, r, donnees)
        for champ, valeur in donnees.items():
            setattr(element, champ, valeur)
        _commettre(db, r, donnees, sauf_id=id_element)
        db.refresh(element)
        return r.public.model_validate(element)

    @routeur.delete("/{id_element}", status_code=status.HTTP_204_NO_CONTENT)
    def supprimer(id_element: int, db: SessionSQL = Depends(get_db)):
        element = _exiger(db, r, id_element)
        par = est_reference(db, element)
        if par is not None:
            raise erreurs.reference_utilisee(r.designation, par)

        db.delete(element)
        try:
            db.commit()
        except IntegrityError as exc:
            # DEUXIEME SERRURE. `est_reference()` lit, puis on supprime : entre
            # les deux, une ligne fille peut naitre. C'est alors SQLite qui
            # refuse — et le contrat a deja le bon code pour ca. Laisser
            # remonter l'exception rendait 500 sur un cas que le front sait
            # traiter. Etroit sur un poste mono-utilisateur ; la demo publique,
            # elle, ne l'est pas.
            db.rollback()
            raise erreurs.reference_utilisee(r.designation, "un autre element") from exc
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return routeur


RESSOURCES: tuple[Ressource, ...] = (
    Ressource(
        chemin="/machines",
        etiquette="machines",
        modele=Machine,
        ecriture=sch.MachineEcriture,
        remplacement=sch.MachineRemplacement,
        public=sch.MachinePublic,
        designation="cette machine",
        cles_uniques=(CleUnique(("nom",), "ce nom"),),
    ),
    Ressource(
        chemin="/cylindres",
        etiquette="cylindres",
        modele=Cylindre,
        ecriture=sch.CylindreEcriture,
        remplacement=sch.CylindreRemplacement,
        public=sch.CylindrePublic,
        designation="ce cylindre",
        # Le repere est grave sur la machine : il est unique CHEZ ELLE, pas
        # dans tout l'atelier.
        cles_uniques=(
            CleUnique(("machine_id", "repere_machine"), "ce repere sur cette machine"),
        ),
        cles_etrangeres=(CleEtrangere("machine_id", Machine),),
    ),
    Ressource(
        chemin="/matieres",
        etiquette="matieres",
        modele=Matiere,
        ecriture=sch.MatiereEcriture,
        remplacement=sch.MatiereRemplacement,
        public=sch.MatierePublic,
        designation="cette matiere",
        cles_uniques=(CleUnique(("nom",), "ce nom"),),
    ),
    Ressource(
        chemin="/outils",
        etiquette="outils",
        modele=Outil,
        ecriture=sch.OutilEcriture,
        remplacement=sch.OutilRemplacement,
        public=sch.OutilPublic,
        designation="cet outil",
        cles_uniques=(CleUnique(("reference",), "cette reference"),),
        cles_etrangeres=(CleEtrangere("cylindre_id", Cylindre),),
    ),
    Ressource(
        chemin="/clients",
        etiquette="clients",
        modele=Client,
        ecriture=sch.ClientEcriture,
        remplacement=sch.ClientRemplacement,
        public=sch.ClientPublic,
        designation="ce client",
        cles_uniques=(CleUnique(("nom",), "ce nom"),),
    ),
    Ressource(
        chemin="/options",
        etiquette="options",
        modele=Option,
        ecriture=sch.OptionEcriture,
        remplacement=sch.OptionRemplacement,
        public=sch.OptionPublic,
        designation="cette option",
        cles_uniques=(CleUnique(("code",), "ce code"),),
    ),
)

routeurs: tuple[APIRouter, ...] = tuple(creer_routeur(r) for r in RESSOURCES)
