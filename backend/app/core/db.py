from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    # Import registers the tables on SQLModel.metadata before create_all.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
