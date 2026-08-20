# -*- coding: utf-8 -*-
"""Primitives de securite — **bibliotheque standard uniquement**.

Aucune dependance ajoutee, et ce n'est pas un principe abstrait : ces modules
partent chez le client dans un **Python embarque**, ou seuls des wheels
binaires peuvent entrer. Une bibliotheque de hachage qui compile a
l'installation bloquerait une imprimerie un dimanche soir.

Deux choses ici, et deux seulement :

- **hachage de mot de passe** — PBKDF2-HMAC-SHA256 avec sel aleatoire. Le
  nombre d'iterations est ecrit DANS la valeur stockee : le jour ou on
  l'augmente, les anciens mots de passe restent verifiables.
- **jetons de session** — tires au hasard, et **stockes haches**. Le jeton en
  clair n'existe que dans le cookie du navigateur ; une lecture de la base ne
  permet pas de se faire passer pour quelqu'un.
"""
import hashlib
import hmac
import secrets

_ALGO = "sha256"
# >= 600 000 : recommandation OWASP courante pour PBKDF2-HMAC-SHA256.
_ITERATIONS = 600_000
_SEL_OCTETS = 16
_JETON_OCTETS = 32


# --- Mot de passe -----------------------------------------------------------


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Rend `pbkdf2_sha256$<iterations>$<sel_hex>$<empreinte_hex>`."""
    sel = secrets.token_bytes(_SEL_OCTETS)
    dk = hashlib.pbkdf2_hmac(_ALGO, mot_de_passe.encode("utf-8"), sel, _ITERATIONS)
    return f"pbkdf2_{_ALGO}${_ITERATIONS}${sel.hex()}${dk.hex()}"


def verifier_mot_de_passe(mot_de_passe: str, stocke: str) -> bool:
    """Comparaison a temps constant. Toute valeur malformee est un echec."""
    try:
        schema, iterations_s, sel_hex, empreinte_hex = stocke.split("$")
        algo = schema.split("_", 1)[1]
        iterations = int(iterations_s)
        sel = bytes.fromhex(sel_hex)
        attendu = bytes.fromhex(empreinte_hex)
    except (ValueError, IndexError):
        return False
    dk = hashlib.pbkdf2_hmac(algo, mot_de_passe.encode("utf-8"), sel, iterations)
    return hmac.compare_digest(dk, attendu)


# --- Jeton de session -------------------------------------------------------


def nouveau_jeton() -> str:
    """Jeton de session en clair. Il n'est JAMAIS ecrit en base."""
    return secrets.token_urlsafe(_JETON_OCTETS)


def empreinte_jeton(jeton: str) -> str:
    """Ce qu'on stocke a la place du jeton.

    SHA-256 nu et non PBKDF2 : un jeton de 32 octets tires au hasard n'a rien a
    craindre d'une attaque par dictionnaire, et cette empreinte est calculee a
    CHAQUE requete authentifiee. 600 000 iterations par appel d'API seraient
    payees pour rien.
    """
    return hashlib.sha256(jeton.encode("utf-8")).hexdigest()
