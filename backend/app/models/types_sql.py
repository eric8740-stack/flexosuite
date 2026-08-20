# -*- coding: utf-8 -*-
"""Un type SQL pour les decimaux — parce que SQLite n'en a pas.

SQLite ne connait que INTEGER, REAL et TEXT. Le type `Numeric` de SQLAlchemy y
passe donc par un **flottant**, et SQLAlchemy previent lui-meme que la precision
n'est pas garantie. Sur une application de devis, ce n'est pas negociable : le
moteur travaille en `Decimal` et les montants dores tombent au centime.

On stocke donc la valeur en **TEXTE**, telle qu'elle a ete calculee.

⚠️ **Limite assumee** : un tri SQL sur une de ces colonnes serait
lexicographique ("9.00" > "10.00"). Aucun tri n'est fait dessus — et le jour ou
il en faudrait un, il se fera en Python, sur les `Decimal` rendus ici.
"""
from decimal import Decimal

from sqlalchemy import String, TypeDecorator


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
