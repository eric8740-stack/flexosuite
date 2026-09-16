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

    assert TABLES_REFERENTIELS <= apres_montee
    # La descente ne retire QUE le lot 2b : le noyau reste debout, sinon une
    # mise a jour ratee chez le client emporterait les comptes avec elle.
    assert not (TABLES_REFERENTIELS & apres_descente)
    assert TABLES_NOYAU <= apres_descente
    assert TABLES_REFERENTIELS <= apres_remontee


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
