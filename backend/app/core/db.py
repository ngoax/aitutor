from collections.abc import Generator
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from app.core.config import settings

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


def init_db() -> None:
    """Bring the database up to the latest migration.

    Runs on startup rather than as a separate command: this is a single local
    instance, so there is no race, and a teacher who pulls an update should not
    have to know what a migration is. `create_all` was not enough because it
    creates missing tables but never adds a column to one that already exists.
    """
    from alembic import command
    from alembic.config import Config

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    command.upgrade(Config(str(ALEMBIC_INI)), "head")


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
