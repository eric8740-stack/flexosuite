# -*- coding: utf-8 -*-
"""Les quatre baremes existent toujours — quitte a les creer en arrivant.

**Pourquoi pas dans la migration, ni a l'installation :**

- une migration qui insere des donnees ne sait pas quoi faire quand la ligne
  existe deja, et elle ne rattrape pas une base creee **avant** elle. Or le lot
  2a est deja sur `main` et peut avoir ete installe ;
- les poser a l'installation creerait une dependance d'ordre entre l'assistant
  d'installation et les baremes — et une installation faite avant ce lot
  resterait sans baremes, pour toujours.

Les creer a la volee est **idempotent** et se repare tout seul : une ligne
manquante ne peut jamais casser un ecran.
"""
from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.orm import Session as SessionSQL

from app.models import DONNEES_NEUTRES, TYPES_BAREMES, Bareme


def assurer_baremes(db: SessionSQL) -> None:
    """Cree les baremes manquants, en mode neutre. Ne touche pas aux autres."""
    existants = set(db.execute(select(Bareme.type)).scalars())
    manquants = [(code, libelle) for code, libelle in TYPES_BAREMES if code not in existants]
    if not manquants:
        return

    for code, libelle in manquants:
        db.add(
            Bareme(
                type=code,
                libelle=libelle,
                machines_ids=[],
                # Copie PROFONDE : `DONNEES_NEUTRES` porte une liste, et la
                # partager entre quatre lignes ferait qu'en calibrer une les
                # calibrerait toutes.
                donnees=deepcopy(DONNEES_NEUTRES),
                actif=True,
            )
        )
    db.commit()
