from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlmodel import Session

from app.core.db import SessionDep, engine
from app.generation.persist import persist_draft, slugify, unique_problem_id
from app.generation.pipeline import generate_draft
from app.llm.provider_config import ProviderConfig
from app.models import DraftStatus, Problem, Project
from app.schemas.draft import ProblemDraftRead
from app.schemas.generation import GenerationRequest

router = APIRouter(prefix="/projects/{project_id}/drafts", tags=["generation"])


def _run_generation(
    problem_id: int, request: GenerationRequest, config: ProviderConfig | None
) -> None:
    """Background entrypoint, so it opens its own session."""
    with Session(engine) as session:
        problem = session.get(Problem, problem_id)
        if problem is None:
            return
        try:
            draft = generate_draft(request, project_id=problem.project_id, config=config)
            persist_draft(session, problem, request, draft)
        except Exception as exc:
            # Surfaced to the teacher through the polled draft rather than raised:
            # nobody is waiting on this request any more.
            problem.status = DraftStatus.FAILED
            problem.error = f"{type(exc).__name__}: {exc}"
            session.add(problem)
            session.commit()


@router.post("", response_model=ProblemDraftRead, status_code=status.HTTP_202_ACCEPTED)
def start_generation(
    project_id: int,
    payload: GenerationRequest,
    session: SessionDep,
    background_tasks: BackgroundTasks,
) -> Problem:
    """Begin generating a problem and return the placeholder row to poll."""
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    config = None
    if project.chat_provider:
        config = ProviderConfig(provider=project.chat_provider, model=project.chat_model)

    # The id comes from the topic, not the generated title, because the row has to
    # exist before there is a title. It is also the more stable of the two: the
    # same topic keeps its slug across regenerations.
    problem = Problem(
        project_id=project_id,
        oatutor_id=unique_problem_id(session, project_id, slugify(payload.topic)),
        title=payload.topic,
        topic=payload.topic,
        difficulty=payload.difficulty,
        status=DraftStatus.GENERATING,
    )
    session.add(problem)
    session.commit()
    session.refresh(problem)

    background_tasks.add_task(_run_generation, problem.id, payload, config)
    return problem


@router.get("/{problem_id}", response_model=ProblemDraftRead)
def get_draft(project_id: int, problem_id: int, session: SessionDep) -> Problem:
    problem = session.get(Problem, problem_id)
    if problem is None or problem.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return problem
