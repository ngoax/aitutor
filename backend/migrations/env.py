"""Alembic environment.

The URL and metadata come from the app rather than alembic.ini so there is one
definition of each: `settings.database_url` and the SQLModel table registry.
"""

from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel, create_engine

import app.models  # noqa: F401  importing registers every table on the metadata
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(settings.database_url)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite cannot ALTER a column in place, so rewrite the table instead.
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
