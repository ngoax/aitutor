from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import (
    context,
    drafts,
    export,
    generation,
    health,
    hints,
    problems,
    projects,
    providers,
    retrieval,
    runs,
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
            # A draft with steps only lost a regeneration, so it keeps them.
            problem.status = DraftStatus.EDITED if problem.steps else DraftStatus.FAILED
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


class _SpaFiles(StaticFiles):
    """Static files that fall back to index.html.

    The React router owns paths the server knows nothing about, so a deep link
    or a refresh must return the app rather than a 404.
    """

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            return await super().get_response("index.html", scope)


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
    app.include_router(context.router, prefix="/api")
    app.include_router(problems.router, prefix="/api")
    app.include_router(steps.router, prefix="/api")
    app.include_router(hints.router, prefix="/api")
    app.include_router(uploads.router, prefix="/api")
    app.include_router(retrieval.router, prefix="/api")
    app.include_router(providers.router, prefix="/api")
    app.include_router(generation.router, prefix="/api")
    app.include_router(drafts.router, prefix="/api")
    app.include_router(drafts.step_router, prefix="/api")
    app.include_router(runs.router, prefix="/api")
    app.include_router(export.router, prefix="/api")

    # Mounted last so it never shadows /api. Absent in local dev, where Vite
    # serves the frontend on its own port.
    if settings.static_dir is not None and settings.static_dir.is_dir():
        app.mount("/", _SpaFiles(directory=settings.static_dir, html=True), name="frontend")
    return app


app = create_app()
