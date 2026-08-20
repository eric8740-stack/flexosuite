r"""Environnement Alembic - l'URL vient TOUJOURS de l'application.

Le fichier .ini ne porte aucune URL : chez le client, la base vit dans
%ProgramData%\FlexoSuite et le chemin est pose par `_env.bat`.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import DATABASE_URL
from app.database import Base
import app.models  # noqa: F401  (enregistre les tables sur Base.metadata)

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def rendre_type(type_, autogen_context):
    """Rend les types MAISON avec leur equivalent SQLAlchemy.

    Sans cela, l'autogeneration ecrit `app.models.types_sql.DecimalTexte(...)`
    dans la migration : elle importerait alors le code de l'application, et une
    migration deja appliquee chez un client se mettrait a dependre d'un module
    qu'on est libre de renommer demain. Une migration doit rester lisible et
    executable telle quelle, des annees plus tard.

    `DecimalTexte` s'appuie sur `String` : le DDL produit est identique.
    """
    if type_.__class__.__name__ == "DecimalTexte":
        return "sa.String(length=%d)" % type_.length if type_.length else "sa.String()"
    return False


def rendre_item(type_objet, objet, autogen_context):
    if type_objet == "type":
        return rendre_type(objet, autogen_context)
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
        render_item=rendre_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            render_item=rendre_item,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
