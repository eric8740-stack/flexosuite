# -*- coding: utf-8 -*-
"""L'aller-retour de migration, joue POUR DE VRAI sur une base vierge.

Pourquoi un sous-processus plutot qu'un appel a l'API d'Alembic : c'est
exactement la commande que joue `install.bat` chez le client, avec la meme
resolution d'URL depuis l'environnement. Un test qui passerait par un chemin
different validerait un chemin que personne n'emprunte.

Pourquoi l'etat se constate avec `sqlite3` et pas avec la sortie d'Alembic :
**on ne demande pas a la commande si elle a reussi, on va regarder.** Alembic
peut rendre 0 en ayant estampille une revision sans creer la table — c'est
precisement le defaut qu'un `git mv` malheureux ou un modele non importe dans
`app/models/__init__.py` produit, et il est invisible dans le journal.
"""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent

TABLES_REFERENTIELS = {"machine", "cylindre", "matiere", "outil", "client", "option"}
TABLES_NOYAU = {"utilisateur", "session_utilisateur", "parametres_couts"}
# La DERNIERE migration en date. C'est elle, et elle seule, que `downgrade -1`
# defait — d'ou la constante : le jour ou une migration s'ajoute, ce test doit
# etre relu, pas rafistole.
TABLES_DERNIERE_MIGRATION = {"bareme"}


def _alembic(base: Path, *arguments: str) -> None:
    environnement = {**os.environ, "DATABASE_URL": f"sqlite:///{base.as_posix()}"}
    acheve = subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND,
        env=environnement,
        capture_output=True,
        text=True,
    )
    # Le code de retour se lit ICI, avant toute mise en forme.
    assert acheve.returncode == 0, (
        f"alembic {' '.join(arguments)} a rendu {acheve.returncode}\n"
        f"--- sortie ---\n{acheve.stdout}\n--- erreurs ---\n{acheve.stderr}"
    )


def _tables(base: Path) -> set[str]:
    """Chemin INDEPENDANT : on ouvre le fichier et on lit son catalogue."""
    connexion = sqlite3.connect(base)
    try:
        lignes = connexion.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    finally:
        connexion.close()
    return {ligne[0] for ligne in lignes}


def _schema(base: Path) -> list[tuple[str, str, str]]:
    """Le DDL COMPLET : tables, index, et le texte de chaque definition.

    Constat 3 de l'audit du 16/09/2026. Comparer des NOMS DE TABLES ne prouve
    presque rien : un `downgrade` qui oublierait un index, une contrainte
    `UNIQUE` ou une cle etrangere laisserait le test au vert. Ce qu'on veut
    savoir, c'est si la base **est la meme**, pas si elle a le meme nombre de
    tables.

    `alembic_version` est ecarte : son contenu change a chaque etape, c'est
    normal, et ce n'est pas le schema de l'application.
    """
    connexion = sqlite3.connect(base)
    try:
        lignes = connexion.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' AND name <> 'alembic_version' "
            "ORDER BY type, name"
        ).fetchall()
    finally:
        connexion.close()
    # Le texte du DDL est normalise sur les espaces : Alembic peut le remettre
    # en forme sans rien changer au schema.
    return [(t, n, " ".join((s or "").split())) for t, n, s in lignes]


@pytest.fixture
def base_neuve(tmp_path):
    return tmp_path / "aller-retour.db"


def test_l_aller_retour_de_migration_se_joue_sur_une_base_vierge(base_neuve):
    _alembic(base_neuve, "upgrade", "head")
    apres_montee = _tables(base_neuve)

    _alembic(base_neuve, "downgrade", "-1")
    apres_descente = _tables(base_neuve)

    _alembic(base_neuve, "upgrade", "head")
    apres_remontee = _tables(base_neuve)

    attendues = TABLES_NOYAU | TABLES_REFERENTIELS | TABLES_DERNIERE_MIGRATION
    assert attendues <= apres_montee
    # La descente ne defait QUE la derniere migration : tout le reste tient
    # debout. Une mise a jour ratee chez le client ne doit pas emporter les
    # comptes ni le parc avec elle.
    assert not (TABLES_DERNIERE_MIGRATION & apres_descente)
    assert (TABLES_NOYAU | TABLES_REFERENTIELS) <= apres_descente
    assert attendues <= apres_remontee


def test_le_schema_revient_a_l_IDENTIQUE_apres_l_aller_retour(base_neuve):
    """Ce que le test precedent n'a jamais prouve.

    Il compte des tables ; celui-ci compare le **DDL complet** — index,
    contraintes `UNIQUE`, cles etrangeres, nullabilite. C'est la difference
    entre « les tables sont revenues » et « la base est la meme ».
    """
    _alembic(base_neuve, "upgrade", "head")
    avant = _schema(base_neuve)

    _alembic(base_neuve, "downgrade", "-1")
    _alembic(base_neuve, "upgrade", "head")
    apres = _schema(base_neuve)

    assert apres == avant
    # Et le contrôle sait dire 1 : il doit voir des index, pas seulement des
    # tables — sinon il comparerait deux listes vides sans que ca se voie.
    assert any(objet[0] == "index" for objet in avant), avant
    assert any("UNIQUE" in objet[2] for objet in avant), avant


def test_le_downgrade_detruit_les_donnees_et_ce_n_est_PAS_un_defaut(base_neuve):
    """La reversibilite constatee est STRUCTURELLE, pas une restauration.

    Releve par l'audit du 16/09/2026, et ecrit ici parce que c'est le genre de
    chose qu'on decouvre en la jouant chez un client : le schema revient, les
    lignes non. Un `downgrade` sur une installation en service efface le parc.
    """
    _alembic(base_neuve, "upgrade", "head")
    connexion = sqlite3.connect(base_neuve)
    connexion.execute(
        "INSERT INTO machine (nom, laize_utile_mm, laize_maxi_mm, "
        "vitesse_moyenne_m_h, duree_calage_h, nb_groupes_couleurs, modules, "
        "diametre_bobine_maxi_mm, temps_changement_bobine_h, actif) "
        "VALUES ('essai', '1', '1', 1, '1', 1, '[]', '1', '1', 1)"
    )
    connexion.commit()
    connexion.close()

    _alembic(base_neuve, "downgrade", "-1")
    _alembic(base_neuve, "upgrade", "head")

    connexion = sqlite3.connect(base_neuve)
    try:
        restant = connexion.execute("SELECT COUNT(*) FROM machine").fetchone()[0]
    finally:
        connexion.close()
    assert restant == 0


def test_la_table_d_une_cle_etrangere_porte_bien_sa_contrainte(base_neuve):
    """SQLite n'applique pas les cles etrangeres par defaut : si la contrainte
    n'etait pas dans le DDL, rien ne le signalerait — la base accepterait des
    orphelins en silence le jour ou la garde applicative sauterait."""
    _alembic(base_neuve, "upgrade", "head")

    connexion = sqlite3.connect(base_neuve)
    try:
        cylindre = connexion.execute("PRAGMA foreign_key_list('cylindre')").fetchall()
        outil = connexion.execute("PRAGMA foreign_key_list('outil')").fetchall()
    finally:
        connexion.close()

    assert [ligne[2] for ligne in cylindre] == ["machine"]
    assert [ligne[2] for ligne in outil] == ["cylindre"]


def test_une_seule_tete_de_migration(base_neuve):
    """Deux tetes = une migration qui ne s'appliquera pas chez le client, et
    personne ne le voit avant l'installation. La CI le verifie aussi ; ici, le
    defaut se voit des le poste de developpement."""
    environnement = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{base_neuve.as_posix()}",
    }
    acheve = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=BACKEND,
        env=environnement,
        capture_output=True,
        text=True,
    )

    assert acheve.returncode == 0, acheve.stderr
    assert acheve.stdout.count("(head)") == 1, acheve.stdout
