# -*- coding: utf-8 -*-
"""Garde-fou de confidentialite — un test de CE QU'ON LIVRE.

Pourquoi ce test existe
-----------------------
FlexoSuite est livre a des imprimeurs et son depot est PUBLIC. Les formules de
chiffrage sont de la convention professionnelle : elles se publient. Les
*valeurs* — taux horaire machine, taux operateur, forfait de calage, prix des
cliches, courbes des baremes — sont l'economie d'un atelier reel. Elles ne se
publient pas, et surtout : elles ne se livrent pas au client suivant, dont le
parc de presses est different. Un devis calcule sur les coefficients de
quelqu'un d'autre est un devis faux.

Pourquoi ce n'est PAS une liste de mots interdits
-------------------------------------------------
Ecrire ici les valeurs a proscrire les publierait — le test qui protege
deviendrait la fuite. On verifie donc la propriete inverse, qui est verifiable
sans jamais nommer ce qu'on protege :

  1. l'application se livre A ZERO TARIF ;
  2. toute valeur chiffree de tarif vit dans UN SEUL module de fixtures
     fictives, hors du code livre.

Ces deux proprietes s'enoncent avec des noms de champs — qui sont les notres,
publics et sans secret.
"""
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

# Le SEUL endroit du depot ou une valeur de tarif a le droit d'etre ecrite.
MODULE_FIXTURES = RACINE / "tests" / "fixtures" / "atelier_demo.py"

# Repertoires balayes : tout ce qui part chez le client, plus le code de test.
RACINES_SOURCES = ("backend", "deploy", "tests")

# Champs qui portent une valeur d'atelier. Les nommer ne revele rien : ce sont
# nos noms de colonnes, ils sont dans le schema public.
CHAMPS_TARIFAIRES = (
    "cout_exploitation_machine_eur_h",
    "cout_operateur_eur_h",
    "cout_energies_eur_h",
    "cout_fixe_atelier_eur_mois",
    "cout_fixe_maintenance_eur_mois",
    "cliche_prix_couleur_eur",
    "outil_base_eur",
    "outil_par_trace_eur",
    "surcout_forme_speciale_facteur",
    "calage_forfait_eur",
    "finitions_prix_m2_eur",
    "prix_kg_defaut",
    "prix_m2_eur",
    "ratio_g_m2_couleur",
    "vitesse_moyenne_m_h",
    "duree_calage_h",
)

# `marge_standard_pct` est traite a part : c'est le SEUL parametre chiffre qui
# se livre, parce que c'est une decision commerciale (30 %) et non un tarif
# d'atelier — et l'imprimeur la confirme explicitement a l'installation.
MARGE_LIVREE_PCT = 30

# Une affectation de valeur : `champ = 12`, `champ: 12`, `champ=Decimal("12")`.
def _motif(champ: str) -> re.Pattern:
    return re.compile(
        rf"""\b{re.escape(champ)}\b\s*[=:]\s*
            (?:Decimal\s*\(\s*["']?)?      # Decimal("12") ou Decimal(12)
            [-+]?\d""",
        re.X,
    )


def _fichiers_python():
    for racine in RACINES_SOURCES:
        base = RACINE / racine
        if not base.exists():
            continue
        for chemin in base.rglob("*.py"):
            if MODULE_FIXTURES.exists() and chemin.samefile(MODULE_FIXTURES):
                continue
            parties = set(chemin.parts)
            if parties & {"__pycache__", ".venv", "venv", "node_modules"}:
                continue
            yield chemin


def test_aucune_valeur_de_tarif_hors_du_module_de_fixtures():
    """Une valeur de tarif ecrite en dur ailleurs que dans les fixtures est,
    par construction, une valeur qu'on livre au client. Elle n'a pas a exister.
    """
    fautes = []
    for chemin in _fichiers_python():
        texte = chemin.read_text(encoding="utf-8", errors="replace")
        for champ in CHAMPS_TARIFAIRES:
            for m in _motif(champ).finditer(texte):
                ligne = texte.count("\n", 0, m.start()) + 1
                fautes.append(f"{chemin.relative_to(RACINE)}:{ligne} — {champ}")

    assert not fautes, (
        "Valeur(s) de tarif ecrite(s) en dur hors du module de fixtures.\n"
        "L'application se livre A ZERO TARIF : les tarifs sont produits chez le\n"
        "client par l'assistant de calibration, jamais herites d'un autre atelier.\n"
        "Deplacer ces valeurs dans tests/fixtures/atelier_demo.py.\n\n"
        + "\n".join(f"  - {f}" for f in fautes)
    )


def test_la_marge_est_le_seul_chiffre_livre():
    """Documente et verrouille l'unique exception : la marge par defaut.

    Ce n'est pas un tarif d'atelier mais une decision commerciale, et
    l'installation la fait confirmer explicitement par l'imprimeur — aucun devis
    ne se calcule sur une marge qu'il n'a jamais vue.
    """
    assert MARGE_LIVREE_PCT == 30
