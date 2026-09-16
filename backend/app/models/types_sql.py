# -*- coding: utf-8 -*-
"""Des types SQL maison — parce que SQLite n'a ni decimal ni JSON.

SQLite ne connait que INTEGER, REAL et TEXT. Le type `Numeric` de SQLAlchemy y
passe donc par un **flottant**, et SQLAlchemy previent lui-meme que la precision
n'est pas garantie. Sur une application de devis, ce n'est pas negociable : le
moteur travaille en `Decimal` et les montants dores tombent au centime.

On stocke donc la valeur en **TEXTE**, telle qu'elle a ete calculee.

⚠️ **Limite assumee** : un tri SQL sur une de ces colonnes serait
lexicographique ("9.00" > "10.00"). Aucun tri n'est fait dessus — et le jour ou
il en faudrait un, il se fera en Python, sur les `Decimal` rendus ici.
"""
import json
from decimal import Decimal

from sqlalchemy import String, Text, TypeDecorator


class DecimalTexte(TypeDecorator):
    """`Decimal` <-> TEXT, sans passer par un flottant."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ARG002
        if value is None:
            return None
        return str(Decimal(str(value)))

    def process_result_value(self, value, dialect):  # noqa: ARG002
        if value is None:
            return None
        return Decimal(value)


class JsonTexte(TypeDecorator):
    """Liste ou objet Python <-> TEXT contenant du JSON.

    Le contrat porte trois champs de forme libre — `machine.modules`,
    `option.modules_requis` et `option.tarification`. Une table de jointure pour
    des listes de codes que personne n'interroge en SQL couterait trois tables de
    plus, et le lot 2c les lit **toujours en bloc**.

    `ensure_ascii=False` : les libelles sont en francais, les ecrire en
    sequences d'echappement rendrait la base illisible a l'oeil nu — et une base
    SQLite chez un client finit toujours par etre ouverte a la main.

    ⚠️ Meme limite que ci-dessus, et pour la meme raison : **aucune requete SQL
    ne filtre sur ces colonnes**. Le filtrage se fait en Python, sur l'objet
    rendu ici.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):  # noqa: ARG002
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    def process_result_value(self, value, dialect):  # noqa: ARG002
        if value is None:
            return None
        return json.loads(value)
