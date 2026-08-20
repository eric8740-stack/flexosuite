# -*- coding: utf-8 -*-
"""Reinitialise le mot de passe administrateur.

Appele par `deploy/windows/reinitialiser-mot-de-passe.bat`. Le mot de passe
n'etant stocke que hache, c'est le SEUL chemin de secours du client : sans lui,
un mot de passe perdu impose une intervention manuelle dans la base.

Le nouveau mot de passe est saisi au clavier, jamais passe en argument : une
ligne de commande se retrouve dans l'historique du shell.

**Toutes les sessions ouvertes sont revoquees.** Reinitialiser un mot de passe
en laissant vivre les sessions existantes ne protegerait de rien : le poste
laisse ouvert dans l'atelier continuerait a fonctionner.
"""
import getpass
import sys
from typing import Callable

from sqlalchemy import select

from app import securite
from app.database import SessionLocale
from app.models import SessionUtilisateur, Utilisateur, maintenant

LONGUEUR_MINI = 8


def main(lire: Callable[[str], str] = getpass.getpass) -> int:
    db = SessionLocale()
    try:
        utilisateurs = db.execute(select(Utilisateur).order_by(Utilisateur.id)).scalars().all()
        if not utilisateurs:
            print(
                "Aucun compte n'existe dans cette base : il n'y a rien a\n"
                "reinitialiser. Ouvrez l'application et faites l'installation.",
                file=sys.stderr,
            )
            return 1
        if len(utilisateurs) > 1:
            # Mono-tenant : ce cas ne doit pas exister. S'il se presente, on
            # refuse plutot que de deviner lequel des comptes reinitialiser.
            print(
                f"{len(utilisateurs)} comptes trouves alors qu'un seul est prevu.\n"
                "Arret : ce script ne devine pas lequel reinitialiser.",
                file=sys.stderr,
            )
            return 1

        utilisateur = utilisateurs[0]
        print(f"Compte concerne : {utilisateur.identifiant}")

        nouveau = lire("Nouveau mot de passe : ")
        if len(nouveau) < LONGUEUR_MINI:
            print(
                f"Mot de passe trop court : {LONGUEUR_MINI} caracteres au minimum.",
                file=sys.stderr,
            )
            return 1
        if nouveau != lire("Confirmez le mot de passe : "):
            print("Les deux saisies different. Rien n'a ete modifie.", file=sys.stderr)
            return 1

        utilisateur.mot_de_passe_hache = securite.hacher_mot_de_passe(nouveau)

        # Revocation en masse : un mot de passe change doit fermer les portes
        # deja ouvertes, sinon il ne change rien pour qui est deja entre.
        ouvertes = db.execute(
            select(SessionUtilisateur).where(SessionUtilisateur.revoquee_le.is_(None))
        ).scalars().all()
        for session in ouvertes:
            session.revoquee_le = maintenant()

        db.commit()
        print(
            f"Mot de passe reinitialise. {len(ouvertes)} session(s) ouverte(s) revoquee(s)."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
