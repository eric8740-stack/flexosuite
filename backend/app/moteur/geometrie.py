# -*- coding: utf-8 -*-
"""La chaine de pose — du format d'etiquette au metrage.

Fonctions pures : pas d'entree/sortie, pas de base. C'est la source de verite
geometrique, distincte de la source de verite tarifaire (`moteur.couts`).

Convention non negociable : **X = laize, Y = developpe**, toujours.
"""
import math
from decimal import ROUND_CEILING, Decimal

# Pratique standard flexo : au-dela, ce n'est plus un intervalle utile, c'est de
# la matiere perdue. On accepte des bords perdus sur la bobine plutot qu'une
# plaque etiree sur toute la laize. Ce n'est PAS un reglage d'atelier.
INTERVALLE_LAIZE_MAX_MM = Decimal("5")

# 1 dent = 1/8 de pouce. Convention industrielle, pas une donnee d'atelier.
DENT_MM = Decimal("3.175")


def poses_en_developpe(
    developpe_cylindre_mm: Decimal,
    hauteur_etiquette_mm: Decimal,
    intervalle_dev_min_mm: Decimal,
) -> tuple[int, Decimal] | None:
    """(nombre de poses, intervalle reel) pour un cylindre donne.

    On tente le plancher, puis — si l'intervalle qui en resulte passe sous le
    minimum — **on retire une pose** et on recalcule. Perdre une pose vaut mieux
    que descendre sous l'intervalle minimum : le squelette casserait.

    L'intervalle reel se **redistribue** sur le tour ; il n'est pas fige au
    minimum. Renvoie None si aucune pose ne tient.
    """
    pas = hauteur_etiquette_mm + intervalle_dev_min_mm
    if pas <= 0:
        return None
    nb_poses = int(developpe_cylindre_mm // pas)
    if nb_poses == 0:
        return None
    intervalle = developpe_cylindre_mm / nb_poses - hauteur_etiquette_mm
    if intervalle < intervalle_dev_min_mm:
        nb_poses -= 1
        if nb_poses == 0:
            return None
        intervalle = developpe_cylindre_mm / nb_poses - hauteur_etiquette_mm
    return nb_poses, intervalle


def intervalle_en_laize(
    laize_utile_mm: Decimal,
    largeur_etiquette_mm: Decimal,
    nb_poses_laize: int,
    forcage_mm: Decimal | None = None,
) -> Decimal | None:
    """Intervalle entre colonnes d'etiquettes. None si la variante ne tient pas.

    Le `forcage` traduit la souverainete du deviseur : il **contourne** le
    plafond — certains cas particuliers l'exigent — et seule la faisabilite
    geometrique est alors verifiee.
    """
    espace_dispo = laize_utile_mm - Decimal(nb_poses_laize) * largeur_etiquette_mm
    if espace_dispo < 0:
        return None
    if nb_poses_laize <= 1:
        return Decimal(0)
    if forcage_mm is not None:
        if Decimal(nb_poses_laize - 1) * forcage_mm > espace_dispo:
            return None
        return forcage_mm
    return min(espace_dispo / Decimal(nb_poses_laize - 1), INTERVALLE_LAIZE_MAX_MM)


def laize_plaque(
    largeur_etiquette_mm: Decimal, nb_poses_laize: int, intervalle_laize_mm: Decimal
) -> Decimal:
    """N poses produisent **N-1 intervalles INTERNES**.

    Ce ne sont pas les bords : sur la bobine, les bords sont libres et se
    traitent a l'etape suivante. La confusion coute une laize entiere.
    """
    if nb_poses_laize <= 0:
        return Decimal(0)
    return (
        Decimal(nb_poses_laize) * largeur_etiquette_mm
        + Decimal(nb_poses_laize - 1) * intervalle_laize_mm
    )


def laize_papier(
    laize_plaque_mm: Decimal,
    bord_lateral_mm: Decimal,
    palier_fournisseur_mm: int,
    laize_utile_mm: Decimal | None = None,
    laize_mini_roulable_mm: Decimal = Decimal(0),
) -> Decimal:
    """Laize commandee au fournisseur.

    Plaque + 2 bords, arrondi au **palier superieur** (les matieres se livrent
    par paliers standard), **plafonne** a la laize utile — la presse rogne le
    bord au-dela — puis **planche** a la laize minimale roulable.

    L'ordre compte : plafond d'abord, plancher ensuite.
    """
    if palier_fournisseur_mm <= 0:
        raise ValueError("Le palier fournisseur doit être strictement positif.")
    mini = laize_plaque_mm + Decimal(2) * bord_lateral_mm
    palier = Decimal(palier_fournisseur_mm)
    papier = (mini / palier).to_integral_value(rounding=ROUND_CEILING) * palier
    if laize_utile_mm is not None:
        papier = min(papier, laize_utile_mm)
    return max(papier, laize_mini_roulable_mm)


def chute_par_cote(laize_papier_mm: Decimal, laize_plaque_mm: Decimal) -> Decimal:
    """La plaque est posee CENTREE sur la bobine : pas d'asymetrie."""
    return (laize_papier_mm - laize_plaque_mm) / Decimal(2)


def metrage(
    quantite: int,
    nb_poses_laize: int,
    nb_poses_dev: int,
    developpe_cylindre_mm: Decimal,
) -> int:
    """Metres lineaires passant en machine.

    ⚠️ **DEUX montees successives**, et les confondre fausse quatre postes a la
    fois (matiere, roulage, finitions, main d'oeuvre) :

      1. le nombre de TOURS est plafonne — convention metier : on finit toujours
         le tour entame. Une etiquette de plus qu'un multiple exact coute un tour
         entier ;
      2. le METRAGE lui-meme est ensuite arrondi au metre SUPERIEUR.
    """
    poses_total = nb_poses_laize * nb_poses_dev
    if poses_total <= 0 or quantite <= 0:
        return 0
    nb_tours = math.ceil(quantite / poses_total)
    metres = Decimal(nb_tours) * developpe_cylindre_mm / Decimal(1000)
    return int(metres.to_integral_value(rounding=ROUND_CEILING))


def surface_consommee_m2(ml_total: int, laize_papier_mm: Decimal) -> Decimal:
    return Decimal(ml_total) * laize_papier_mm / Decimal(1000)


def rendement_pct(
    quantite: int,
    largeur_etiquette_mm: Decimal,
    hauteur_etiquette_mm: Decimal,
    surface_consommee_m2_: Decimal,
) -> Decimal:
    """Surface utile / surface consommee. 0 si rien n'est consomme."""
    if surface_consommee_m2_ <= 0:
        return Decimal(0)
    utile = (
        Decimal(quantite) * largeur_etiquette_mm * hauteur_etiquette_mm
        / Decimal(1_000_000)
    )
    return utile / surface_consommee_m2_ * Decimal(100)


def diametre_bobine_mm(
    ml_total: int,
    epaisseur_reelle_microns: Decimal,
    diametre_mandrin_mm: Decimal,
    ) -> int:
    """Diametre exterieur estime, modele volumique (couches jointives).

    ⚠️ L'epaisseur est celle de la matiere **reelle**. Une valeur de repli qui
    ignorerait la matiere est un defaut, pas une commodite : le diametre
    conditionne le nombre de bobines, donc les arrets machine.
    """
    if diametre_mandrin_mm <= 0 or epaisseur_reelle_microns <= 0:
        return 0
    rayon_mandrin = float(diametre_mandrin_mm) / 2
    epaisseur_mm = float(epaisseur_reelle_microns) / 1000
    section = ml_total * 1000 * epaisseur_mm
    rayon = math.sqrt(rayon_mandrin**2 + section / math.pi)
    return round(rayon * 2)
