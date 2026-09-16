# -*- coding: utf-8 -*-
"""La table des six ressources — celle que les tests parametres consomment.

Elle N'EST PAS une copie du routeur : c'est la lecture du **contrat**, ecrite a
la main a partir de `docs/CONTRAT-API.md`. C'est toute la difference entre un
test qui verifie ce que le code fait et un test qui verifie ce que le contrat
promet. Si le routeur et cette table divergent, l'un des deux a tort, et le test
le dit.

Les VALEURS, elles, ne sont pas ici : elles viennent de
`tests/fixtures/atelier_demo.py`, seul module du depot autorise a en porter.
"""
from copy import deepcopy
from dataclasses import dataclass

from tests.fixtures import atelier_demo as demo

# `machine` et `cylindre` : le cas a besoin qu'un parent existe d'abord.
PARENT_MACHINE = "machine"
PARENT_CYLINDRE = "cylindre"


@dataclass(frozen=True)
class CasRessource:
    chemin: str
    # Corps d'ecriture, SANS la cle etrangere : `corps_complet` la pose.
    corps: dict
    # Les cles exactes du JSON rendu, telles que le contrat les ecrit.
    cles_attendues: frozenset
    # Le champ qu'on duplique pour provoquer un 409 `deja_existant`.
    champ_unique: str
    parent: str | None = None
    # Champ de cle etrangere a remplir avec l'identifiant du parent.
    champ_parent: str | None = None

    def __str__(self) -> str:  # identifiant lisible dans la sortie pytest
        return self.chemin.strip("/")


MACHINES = CasRessource(
    chemin="/api/machines",
    corps=demo.MACHINE_DEMO,
    cles_attendues=frozenset(
        {
            "id",
            "nom",
            "laize_utile_mm",
            "laize_maxi_mm",
            "vitesse_moyenne_m_h",
            "duree_calage_h",
            "nb_groupes_couleurs",
            "modules",
            "diametre_bobine_maxi_mm",
            "temps_changement_bobine_h",
            "actif",
        }
    ),
    champ_unique="nom",
)

CYLINDRES = CasRessource(
    chemin="/api/cylindres",
    corps=demo.CYLINDRE_DEMO,
    cles_attendues=frozenset(
        {
            "id",
            "developpe_mm",
            "nb_dents",
            "repere_machine",
            "nb_porte_cliches",
            "machine_id",
            "date_inventaire",
            "actif",
        }
    ),
    champ_unique="repere_machine",
    parent=PARENT_MACHINE,
    champ_parent="machine_id",
)

MATIERES = CasRessource(
    chemin="/api/matieres",
    corps=demo.MATIERE_DEMO,
    cles_attendues=frozenset(
        {"id", "nom", "grammage_g_m2", "prix_m2_eur", "epaisseur_reelle_micron", "actif"}
    ),
    champ_unique="nom",
)

OUTILS = CasRessource(
    chemin="/api/outils",
    corps=demo.OUTIL_DEMO,
    cles_attendues=frozenset(
        {
            "id",
            "reference",
            "largeur_mm",
            "hauteur_mm",
            "nb_poses_laize",
            "nb_poses_developpe",
            "forme_speciale",
            "cylindre_id",
            "actif",
        }
    ),
    champ_unique="reference",
    parent=PARENT_CYLINDRE,
    champ_parent="cylindre_id",
)

CLIENTS = CasRessource(
    chemin="/api/clients",
    corps=demo.CLIENT_DEMO,
    cles_attendues=frozenset(
        {"id", "nom", "contact", "email", "telephone", "intervalle_dev_min_mm", "actif"}
    ),
    champ_unique="nom",
)

OPTIONS = CasRessource(
    chemin="/api/options",
    corps=demo.OPTION_DEMO,
    cles_attendues=frozenset(
        {
            "id",
            "code",
            "libelle",
            "groupes_couleurs_requis",
            "modules_requis",
            "coefficient_vitesse",
            "coefficient_gache",
            "temps_calage_ajoute_h",
            "tarification",
            "silhouette_automatique",
            "actif",
        }
    ),
    champ_unique="code",
)

TOUTES = (MACHINES, CYLINDRES, MATIERES, OUTILS, CLIENTS, OPTIONS)


def creer_machine(client, suffixe: str = "") -> int:
    corps = dict(demo.MACHINE_DEMO)
    corps["nom"] = corps["nom"] + suffixe
    reponse = client.post(MACHINES.chemin, json=corps)
    assert reponse.status_code == 201, reponse.text
    return reponse.json()["id"]


def creer_cylindre(client, suffixe: str = "") -> int:
    corps = dict(demo.CYLINDRE_DEMO)
    corps["machine_id"] = creer_machine(client, suffixe)
    corps["repere_machine"] = corps["repere_machine"] + suffixe
    reponse = client.post(CYLINDRES.chemin, json=corps)
    assert reponse.status_code == 201, reponse.text
    return reponse.json()["id"]


def corps_complet(client, cas: CasRessource, suffixe: str = "") -> dict:
    """Le corps d'ecriture du cas, cle etrangere resolue si besoin.

    `suffixe` sert aux tests qui creent plusieurs elements : il evite un 409
    `deja_existant` la ou ce n'est pas ce qu'on mesure.

    ⚠️ **Copie PROFONDE, et ce n'est pas de la prudence gratuite.** Le corps de
    l'option porte un dictionnaire imbrique (`tarification`). Une copie de
    surface le partagerait avec le module de fixtures : un test qui ecrirait
    `corps["tarification"]["type"] = ...` corromprait la fixture pour TOUS les
    tests suivants de la session, et le premier a echouer ne serait pas le
    coupable.
    """
    corps = deepcopy(cas.corps)
    if cas.parent == PARENT_MACHINE:
        corps[cas.champ_parent] = creer_machine(client, suffixe)
    elif cas.parent == PARENT_CYLINDRE:
        corps[cas.champ_parent] = creer_cylindre(client, suffixe)
    if suffixe:
        corps[cas.champ_unique] = corps[cas.champ_unique] + suffixe
    return corps
