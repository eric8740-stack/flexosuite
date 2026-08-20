"""Reinitialise le mot de passe administrateur.

Appele par `deploy/windows/reinitialiser-mot-de-passe.bat`. Le mot de passe
n'etant stocke que hache, c'est le SEUL chemin de secours du client : sans lui,
un mot de passe perdu impose une intervention manuelle dans la base.

Le nouveau mot de passe est saisi au clavier, jamais passe en argument : une
ligne de commande se retrouve dans l'historique du shell.
"""
import sys


def main() -> int:
    print(
        "L'authentification arrive au lot 2 (donnees et API).\n"
        "Ce script est en place des maintenant parce qu'il fait partie du\n"
        "contrat de livraison : il ne doit pas etre oublie au moment ou le\n"
        "compte administrateur existera.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
