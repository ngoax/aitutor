from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.api.routes import (
    drafts,
    generation,
    health,
    problems,
    projects,
    providers,
    retrieval,
    steps,
    uploads,
)
from app.core.config import settings
from app.core.db import engine, init_db
from app.models import (
    DraftStatus,
    IngestionStatus,
    Problem,
    SourceDocument,
)


def _fail_interrupted_work() -> None:
    """Mark work that a previous process was still doing as failed"""
    with Session(engine) as session:
        problems = session.exec(
            select(Problem).where(Problem.status == DraftStatus.GENERATING)
        ).all()
        documents = session.exec(
            select(SourceDocument).where(SourceDocument.status == IngestionStatus.PENDING)
        ).all()

        for problem in problems:
            problem.status = DraftStatus.FAILED
            problem.error = "Generation was interrupted by a server restart."
            session.add(problem)
        for document in documents:
            document.status = IngestionStatus.FAILED
            document.error = "Extraction was interrupted by a server restart."
            session.add(document)
        session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _fail_interrupted_work()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AITutor — OATutor content authoring", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(problems.router, prefix="/api")
    app.include_router(steps.router, prefix="/api")
    app.include_router(uploads.router, prefix="/api")
    app.include_router(retrieval.router, prefix="/api")
    app.include_router(providers.router, prefix="/api")
    app.include_router(generation.router, prefix="/api")
    app.include_router(drafts.router, prefix="/api")
    return app


app = create_app()
