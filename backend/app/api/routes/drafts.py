from fastapi import APIRouter, HTTPException, status

from app.core.db import SessionDep
from app.generation.persist import persist_draft
from app.generation.pipeline import generate_draft
from app.llm.provider_config import ProviderConfig
from app.models import Problem, Project
from app.schemas.draft import ProblemDraftRead
from app.schemas.generation import GenerationRequest

router = APIRouter(prefix="/projects/{project_id}/generate", tags=["generation"])


@router.post("", response_model=ProblemDraftRead, status_code=status.HTTP_201_CREATED)
def generate(project_id: int, payload: GenerationRequest, session: SessionDep) -> Problem:
    """Generate one problem with its steps and hints, and store it as a draft."""
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    config = None
    if project.chat_provider:
        config = ProviderConfig(provider=project.chat_provider, model=project.chat_model)

    try:
        draft = generate_draft(payload, project_id=project_id, config=config)
    except Exception as exc:
        # Anything raised here is the model provider's failure rather than the
        # caller's: retries exhausted, a rate limit, an unreachable endpoint. A
        # 500 with a traceback tells the teacher nothing they can act on.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return persist_draft(session, project_id, payload, draft)
