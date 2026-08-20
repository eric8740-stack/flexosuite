# -*- coding: utf-8 -*-
"""Les sept postes de cout, et l'assemblage du prix.

⚠️ **L'ARRONDI SE REPRODUIT, IL NE SE NORMALISE PAS.**

Il n'existe pas de regle generale d'arrondi ici, et il ne faut pas en inventer
une : les montants dores ont ete produits par un moteur valide, avec SON
arrondi, incoherences comprises. Un moteur qui « nettoie » la regle rate les
dores d'un centime, et la preuve de non-regression s'effondre.

La carte, poste par poste (cf. § 3 bis de docs/SPEC-METIER.md) :

    P1  un seul arrondi, sur poids x prix au kilo
    P2  les sous-totaux se somment BRUTS, un seul arrondi a la fin
    P3  cliches arrondis, outil arrondi, PUIS leur somme re-arrondie  (3 fois)
    P4  un arrondi sur le forfait (sans effet, deja a 2 decimales)
    P5  un seul arrondi
    P6  la base est arrondie, PUIS base + sous-traitance re-arrondi  (2 fois)
    P7  un seul arrondi
    cout de revient : arrondi AVANT que la marge s'applique
    prix de vente   : arrondi ensuite -> DOUBLE arrondi

P2 et P3 font pourtant la meme chose (sommer des sous-totaux) et ne se
comportent pas pareil ; P6 arrondit sa base avant d'ajouter un forfait, ce que
ne fait aucun autre poste. Ces deux incoherences sont DANS les montants dores.
Les corriger, c'est les manquer. Uniformiser est un chantier separe, sur
decision d'Eric, avec re-baseline explicite.
"""
from decimal import ROUND_HALF_EVEN, Decimal

from app.moteur.types import (
    EntreeChiffrage,
    ParametresCouts,
    PosteCout,
    ResultatChiffrage,
    ResultatMultiLots,
)

CENT = Decimal("0.01")


def arrondi(valeur: Decimal) -> Decimal:
    """Arrondi monetaire du moteur de couts : au pair le plus proche.

    C'est le mode par defaut du type decimal, et c'est celui avec lequel les
    montants dores ont ete produits. Il est ecrit EXPLICITEMENT ici pour qu'un
    changement de contexte d'execution ne le modifie pas en silence.

    ⚠️ Ce n'est pas le seul mode de la chaine : le total d'un devis arrondit au
    superieur a la moitie. Sur une valeur a mi-chemin, les deux divergent d'un
    centime. C'est voulu, et documente.
    """
    return valeur.quantize(CENT, rounding=ROUND_HALF_EVEN)


# --- P1 ----------------------------------------------------------------------
def poste_1_matiere(e: EntreeChiffrage, p: ParametresCouts) -> PosteCout:
    """La matiere se facture sur la laize PAPIER quand elle est connue.

    Le repli sur `laize utile + marge de confort` existe pour les appels qui ne
    portent pas encore la laize papier. Quand elle est fournie, la marge de
    confort n'est PAS ajoutee : elle double-compterait les bords.
    """
    if e.laize_papier_mm is not None:
        laize_facturee = e.laize_papier_mm
        source = "laize_papier"
    else:
        laize_facturee = e.laize_utile_mm + Decimal(p.marge_confort_roulage_mm)
        source = "laize_utile+marge_confort"

    surface_m2 = laize_facturee / Decimal(1000) * Decimal(e.ml_total)
    poids_kg = surface_m2 * e.matiere.grammage_g_m2 / Decimal(1000)
    montant = arrondi(poids_kg * e.matiere.prix_kg_eur)

    return PosteCout(1, "Matière", montant, {
        "laize_facturee_mm": laize_facturee,
        "source_laize": source,
        "surface_support_m2": surface_m2,
        "poids_kg": poids_kg,
        "prix_kg_eur": e.matiere.prix_kg_eur,
    })


# --- P2 ----------------------------------------------------------------------
def poste_2_encres(e: EntreeChiffrage, p: ParametresCouts) -> PosteCout:
    """Les sous-totaux se somment BRUTS — un seul arrondi, a la fin.

    Les consommations par type figurent dans les details pour l'audit : elles ne
    sont PAS arrondies avant d'etre sommees.
    """
    surface_m2 = e.laize_utile_mm / Decimal(1000) * Decimal(e.ml_total)
    total_brut = Decimal(0)
    details: dict = {"surface_imprimee_m2": surface_m2}

    for type_encre, nb_couleurs in e.couleurs_par_type.items():
        if nb_couleurs <= 0:
            continue
        tarif = e.tarifs_encre.get(type_encre)
        if tarif is None:
            # Pas de zero silencieux : un tarif manquant est une erreur de
            # parametrage, pas une encre gratuite.
            raise ValueError(
                f"Aucun tarif pour l'encre {type_encre!r} — completez le paramétrage."
            )
        conso_kg = (
            surface_m2 * Decimal(nb_couleurs) * tarif.ratio_g_m2_couleur / Decimal(1000)
        )
        total_brut += conso_kg * tarif.prix_kg_eur
        details[f"conso_kg_{type_encre}"] = conso_kg
        details[f"nb_couleurs_{type_encre}"] = nb_couleurs

    return PosteCout(2, "Encres", arrondi(total_brut), details)


# --- P3 ----------------------------------------------------------------------
def poste_3_outillage(e: EntreeChiffrage, p: ParametresCouts) -> PosteCout:
    """Cliches et outil arrondis separement, PUIS leur somme re-arrondie.

    Trois arrondis, la ou P2 n'en fait qu'un. C'est l'incoherence assumee.
    """
    nb_couleurs = sum(n for n in e.couleurs_par_type.values() if n > 0)
    cout_cliches = arrondi(Decimal(nb_couleurs) * p.cliche_prix_couleur_eur)

    if e.outil_existant:
        # Outil amorti : pas de re-facturation.
        cout_outil = arrondi(Decimal(0))
    else:
        base = p.outil_base_eur + Decimal(e.nb_traces) * p.outil_par_trace_eur
        if e.forme_speciale:
            cout_outil = arrondi(base * p.surcout_forme_speciale_facteur)
        else:
            cout_outil = arrondi(base)

    return PosteCout(3, "Outillage / Clichés", arrondi(cout_cliches + cout_outil), {
        "nb_couleurs_total": nb_couleurs,
        "cout_cliches_eur": cout_cliches,
        "cout_outil_eur": cout_outil,
        "mode_outil": "existant" if e.outil_existant else "neuf",
    })


# --- P4 ----------------------------------------------------------------------
def poste_4_calage(e: EntreeChiffrage, p: ParametresCouts, nb_calages: int = 1) -> PosteCout:
    """Le calage est lie a l'OUTIL, pas a la bobine.

    Un lot qui reutilise le meme montage ne rajoute pas de calage :
    `nb_calages = 1 + nb_changements`.
    """
    montant = arrondi(p.calage_forfait_eur * Decimal(nb_calages))
    return PosteCout(4, "Mise en route / Calage", montant, {
        "forfait_eur": p.calage_forfait_eur,
        "nb_calages": nb_calages,
    })


# --- P5 ----------------------------------------------------------------------
def poste_5_roulage(e: EntreeChiffrage, p: ParametresCouts) -> PosteCout:
    if e.machine.vitesse_moyenne_m_h <= 0:
        raise ValueError(
            f"La presse {e.machine.nom!r} n'a pas de vitesse moyenne exploitable."
        )
    temps_h = Decimal(e.ml_total) / Decimal(e.machine.vitesse_moyenne_m_h)
    montant = arrondi(temps_h * p.cout_exploitation_machine_eur_h)
    return PosteCout(5, "Roulage", montant, {
        "temps_production_h": temps_h,
        "vitesse_moyenne_m_h": e.machine.vitesse_moyenne_m_h,
    })


# --- P6 ----------------------------------------------------------------------
def poste_6_finitions(e: EntreeChiffrage, p: ParametresCouts) -> PosteCout:
    """La base est arrondie AVANT l'ajout des forfaits de sous-traitance.

    Aucun autre poste ne procede ainsi. C'est dans les montants dores.

    La surface est la surface IMPRIMEE (laize utile), pas la surface support :
    la marge de confort est consommee par le support mais ne recoit pas de
    finition.
    """
    surface_m2 = e.laize_utile_mm / Decimal(1000) * Decimal(e.ml_total)
    base = arrondi(surface_m2 * p.finitions_prix_m2_eur)
    sous_traitance = sum(e.forfaits_sous_traitance, Decimal(0))
    return PosteCout(6, "Finitions", arrondi(base + sous_traitance), {
        "surface_imprimee_m2": surface_m2,
        "cout_base_eur": base,
        "cout_sous_traitance_eur": sous_traitance,
    })


# --- P7 ----------------------------------------------------------------------
def poste_7_main_d_oeuvre(e: EntreeChiffrage, p: ParametresCouts) -> PosteCout:
    """Le temps de calage est remunere ICI **et** compte en P4.

    Ce double-compte est INTENTIONNEL et conforme a la pratique flexo : pendant
    le calage, deux ressources distinctes sont mobilisees — la machine
    immobilisee (P4) et l'humain qui regle (P7). Ne pas « corriger ».
    """
    heures_production = Decimal(e.ml_total) / Decimal(e.machine.vitesse_moyenne_m_h)
    if e.heures_dossier_override is not None:
        heures_total = e.heures_dossier_override
        source = "saisie"
    else:
        heures_total = e.machine.duree_calage_h + heures_production
        source = "derive_machine"
    montant = arrondi(heures_total * p.cout_operateur_eur_h)
    return PosteCout(7, "Main d'œuvre opérateur", montant, {
        "heures_calage": e.machine.duree_calage_h,
        "heures_production": heures_production,
        "heures_total": heures_total,
        "source_heures": source,
    })


# --- Assemblage ---------------------------------------------------------------
def chiffrer(
    e: EntreeChiffrage, p: ParametresCouts, nb_calages: int = 1
) -> ResultatChiffrage:
    """Chiffre un lot. Le cout de revient est arrondi AVANT la marge."""
    postes = [
        poste_1_matiere(e, p),
        poste_2_encres(e, p),
        poste_3_outillage(e, p),
        poste_4_calage(e, p, nb_calages),
        poste_5_roulage(e, p),
        poste_6_finitions(e, p),
        poste_7_main_d_oeuvre(e, p),
    ]
    cout_revient = arrondi(sum((x.montant_eur for x in postes), Decimal(0)))
    coefficient = Decimal(1) + p.marge_standard_pct / Decimal(100)
    return ResultatChiffrage(
        postes=postes,
        cout_revient_eur=cout_revient,
        marge_pct=p.marge_standard_pct,
        coefficient=coefficient,
        prix_vente_ht_eur=arrondi(cout_revient * coefficient),
        nb_calages=nb_calages,
    )


def chiffrer_lots(
    entrees: list[EntreeChiffrage], p: ParametresCouts
) -> ResultatMultiLots:
    """Chiffre plusieurs lots, calage mutualise entre montages identiques.

    Le PREMIER lot porte toujours son calage : son drapeau est ignore, sans quoi
    une saisie fautive facturerait deux calages pour un seul montage. Un lot
    suivant ne garde le sien que sur un vrai changement d'outil ou de cliches.

    Le total est la somme des prix de lot **deja arrondis** : le detail somme
    donc au total par construction, et un deviseur peut defendre son devis ligne
    a ligne.
    """
    resultats: list[ResultatChiffrage] = []
    nb_calages = 0

    for rang, e in enumerate(entrees):
        porte_calage = rang == 0 or e.changement_outil_cliche
        if porte_calage:
            nb_calages += 1
            resultats.append(chiffrer(e, p))
            continue

        # Meme montage : on retire le calage, et on recalcule le prix du lot
        # comme un lot SANS calage — avec le meme arrondi que le moteur.
        complet = chiffrer(e, p)
        calage = next(x.montant_eur for x in complet.postes if x.numero == 4)
        postes = [
            PosteCout(x.numero, x.libelle, Decimal("0.00"), {**x.details, "mutualise": True})
            if x.numero == 4 else x
            for x in complet.postes
        ]
        cout_revient = arrondi(complet.cout_revient_eur - calage)
        resultats.append(ResultatChiffrage(
            postes=postes,
            cout_revient_eur=cout_revient,
            marge_pct=complet.marge_pct,
            coefficient=complet.coefficient,
            prix_vente_ht_eur=arrondi(cout_revient * complet.coefficient),
            nb_calages=0,
            calage_mutualise_eur=calage,
        ))

    return ResultatMultiLots(
        lots=resultats,
        cout_revient_eur=arrondi(sum((r.cout_revient_eur for r in resultats), Decimal(0))),
        prix_vente_ht_eur=arrondi(sum((r.prix_vente_ht_eur for r in resultats), Decimal(0))),
        nb_calages=nb_calages,
    )
