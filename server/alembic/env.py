from logging.config import fileConfig

from geoalchemy2 import alembic_helpers
from sqlalchemy import create_engine, pool

from alembic import context
from src.core.config import settings
from src.models import Base

# The postgis image puts the tiger and topology schemas on the search_path; autogenerate must
# only see the public schema or it tries to drop their tables.
PUBLIC_SCHEMA_ONLY = {"options": "-c search_path=public"}

GEOSPATIAL_OPTIONS = {
    "include_object": alembic_helpers.include_object,
    "process_revision_directives": alembic_helpers.writer,
    "render_item": alembic_helpers.render_item,
}

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=Base.metadata,
        literal_binds=True,
        **GEOSPATIAL_OPTIONS,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        settings.DATABASE_URL, poolclass=pool.NullPool, connect_args=PUBLIC_SCHEMA_ONLY
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=Base.metadata, **GEOSPATIAL_OPTIONS
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
