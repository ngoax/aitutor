from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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
