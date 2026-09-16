# -*- coding: utf-8 -*-
"""Les quatre baremes existent toujours — quitte a les creer en arrivant.

**Pourquoi pas dans la migration, ni a l'installation :**

- une migration qui insere des donnees ne sait pas quoi faire quand la ligne
  existe deja, et elle ne rattrape pas une base creee **avant** elle. Or le lot
  2a est deja sur `main` et peut avoir ete installe ;
- les poser a l'installation creerait une dependance d'ordre entre l'assistant
  d'installation et les baremes — et une installation faite avant ce lot
  resterait sans baremes, pour toujours.

Les creer a la volee est idempotent, y compris sous acces concurrent **depuis
la correction du constat 2** de l'audit du 16/09/2026 — ca ne l'etait pas avant,
et le docstring l'affirmait quand meme.
"""
from copy import deepcopy

from sqlalchemy.dialects.sqlite import insert as insert_sqlite
from sqlalchemy.orm import Session as SessionSQL

from app.models import DONNEES_NEUTRES, TYPES_BAREMES, Bareme


def assurer_baremes(db: SessionSQL) -> None:
    """Cree les baremes manquants, en mode neutre. Ne touche pas aux autres.

    ⚠️ **Aucune lecture prealable, et c'est tout le correctif.** La version
    precedente lisait les types existants, puis inserait les manquants : deux
    requetes qui lisaient avant que l'une ait commite inseraient toutes les
    deux, et la seconde prenait une `IntegrityError` non rattrapee — donc
    **500 sur `GET /api/baremes`**, le premier appel de l'ecran barmes. La
    fenetre est etroite (elle n'existe que tant que des baremes manquent, donc
    une seule fois apres deploiement), mais c'est exactement le moment ou
    plusieurs visiteurs arrivent sur la demo publique.

    On ne **rattrape** pas la course, on la **supprime** : `ON CONFLICT DO
    NOTHING` laisse la base trancher, et il n'y a plus d'intervalle entre le
    constat et l'ecriture. Rien ne reste a traduire en code d'erreur — un 409
    ici dirait « conflit » a un client qui n'a fait que lire.

    ⚠️ **`DO NOTHING`, jamais `DO UPDATE`.** Un `DO UPDATE` — ou un `merge()` —
    rendrait ses donnees neutres, a chaque `GET`, a un bareme que l'imprimeur
    vient de calibrer. Le 500 se voyait ; une courbe remise a zero ne se verrait
    pas.

    Le `commit()` reste, et sa portee reste celle de la session — c'est la
    reserve du constat 7. Elle est sans effet tant que la fonction est appelee
    en **premiere instruction** des routeurs, ce que font les deux appelants.
    Le jour ou l'un la placerait apres une modification metier, c'est l'appelant
    qu'il faudra corriger : `assurer_baremes()` doit persister ses lignes meme
    sur un `GET`, sinon elles se recreeraient a chaque appel.

    Lie au dialecte SQLite, et c'est assume : le profil de livraison est SQLite,
    sans aucun SGBD serveur chez le client.
    """
    lignes = [
        {
            "type": code,
            "libelle": libelle,
            "machines_ids": [],
            # Copie PROFONDE : `DONNEES_NEUTRES` porte une liste, et la partager
            # entre quatre lignes ferait qu'en calibrer une les calibrerait
            # toutes.
            "donnees": deepcopy(DONNEES_NEUTRES),
            "actif": True,
        }
        for code, libelle in TYPES_BAREMES
    ]

    db.execute(
        insert_sqlite(Bareme).on_conflict_do_nothing(index_elements=["type"]),
        lignes,
    )
    db.commit()
