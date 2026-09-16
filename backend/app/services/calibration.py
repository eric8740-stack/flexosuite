# -*- coding: utf-8 -*-
"""Le taux horaire machine — la formule, et rien d'autre.

::

    amortissement_annuel = prix_achat_presse_eur / duree_amortissement_ans

    taux_eur_h = (amortissement_annuel + energie_eur_an + maintenance_eur_an)
                 / heures_productives_par_an

L'assistant ne demande **jamais un tarif a recopier**, seulement des nombres que
l'imprimeur connait : ce qu'il a paye sa presse, sur combien d'annees il
l'amortit, combien d'heures elle tourne, ce que coutent l'energie et la
maintenance. C'est toute la difference entre un tarif herite d'un autre atelier
— qui produit des devis faux — et un tarif qu'il reconnait comme le sien.

**Fonction PURE : elle ne touche pas la base.** Le calcul propose, il
n'enregistre pas ; c'est un `PUT` sur les parametres qui decide. Un assistant
qui ecrirait tout seul retirerait a l'imprimeur la seule chose qui compte ici :
le moment ou il dit oui.

⚠️ **Le taux est la SOMME DES LIGNES ARRONDIES, pas le total arrondi une fois.**
L'ecart est d'un centime au plus, et il est volontaire : le contrat rend le
detail « parce qu'un chiffre qu'on ne sait pas justifier ne sera pas adopte ».
Un imprimeur qui additionne les trois lignes affichees doit retomber sur le taux
affiche. S'il ne retombe pas dessus, c'est l'outil qu'il cesse de croire, pas
son addition.
"""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENTIME = Decimal("0.01")

LIBELLE_AMORTISSEMENT = "Amortissement"
LIBELLE_ENERGIE = "Energie"
LIBELLE_MAINTENANCE = "Maintenance"


@dataclass(frozen=True)
class LigneDetail:
    libelle: str
    montant_eur_h: Decimal


@dataclass(frozen=True)
class Resultat:
    taux_eur_h: Decimal
    detail: tuple[LigneDetail, ...]


def _par_heure(montant_annuel: Decimal, heures: int) -> Decimal:
    return (montant_annuel / Decimal(heures)).quantize(CENTIME, rounding=ROUND_HALF_UP)


def taux_machine(
    prix_achat_presse_eur: Decimal,
    duree_amortissement_ans: int,
    heures_productives_par_an: int,
    energie_eur_an: Decimal,
    maintenance_eur_an: Decimal,
) -> Resultat:
    """Le taux horaire, et son explication ligne par ligne.

    Les deux diviseurs sont supposes strictement positifs : c'est le schema
    d'entree qui le garantit (422 sinon), pas cette fonction. Une garde ici
    dupliquerait la validation a un endroit ou personne ne penserait a la
    relire.
    """
    amortissement_annuel = prix_achat_presse_eur / Decimal(duree_amortissement_ans)

    detail = (
        LigneDetail(
            LIBELLE_AMORTISSEMENT,
            _par_heure(amortissement_annuel, heures_productives_par_an),
        ),
        LigneDetail(
            LIBELLE_ENERGIE, _par_heure(energie_eur_an, heures_productives_par_an)
        ),
        LigneDetail(
            LIBELLE_MAINTENANCE,
            _par_heure(maintenance_eur_an, heures_productives_par_an),
        ),
    )

    return Resultat(
        taux_eur_h=sum((ligne.montant_eur_h for ligne in detail), Decimal("0.00")),
        detail=detail,
    )
