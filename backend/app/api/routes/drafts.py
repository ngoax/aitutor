from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlmodel import Session, select

from app.api.editing import editable_step
from app.core.db import SessionDep, engine
from app.generation.persist import (
    as_generated_problem,
    as_generated_steps,
    persist_draft,
    replace_step,
    slugify,
    unique_problem_id,
)
from app.generation.pipeline import generate_draft, regenerate_step
from app.llm.provider_config import ProviderConfig
from app.models import DraftStatus, Problem, Project, Step
from app.schemas.draft import ProblemDraftRead
from app.schemas.generation import GenerationRequest

router = APIRouter(prefix="/projects/{project_id}/drafts", tags=["generation"])

# Regeneration hangs off the step it replaces, not off the draft as a whole.
step_router = APIRouter(
    prefix="/projects/{project_id}/problems/{problem_id}/steps", tags=["generation"]
)


def _provider_config(project: Project) -> ProviderConfig | None:
    if not project.chat_provider:
        return None
    return ProviderConfig(provider=project.chat_provider, model=project.chat_model)


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

    config = _provider_config(project)

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
        generation_request=payload.model_dump(mode="json"),
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


def _run_regeneration(
    step_id: int, restore_status: DraftStatus, config: ProviderConfig | None
) -> None:
    with Session(engine) as session:
        step = session.get(Step, step_id)
        if step is None:
            return
        problem = step.problem
        problem.status = restore_status
        try:
            request = GenerationRequest(**problem.generation_request)
            earlier = session.exec(
                select(Step)
                .where(Step.problem_id == problem.id, Step.order_index < step.order_index)
                .order_by(Step.order_index)
            ).all()
            draft_step = regenerate_step(
                request=request,
                project_id=problem.project_id,
                problem=as_generated_problem(problem),
                previous_steps=as_generated_steps(earlier),
                step_number=step.order_index + 1,
                config=config,
            )
            replace_step(session, step, draft_step, request.problem_type)
            problem.error = None
        except Exception as exc:
            # Only the attempt failed, not the draft, so the old status is restored.
            problem.error = f"Could not regenerate that step — {type(exc).__name__}: {exc}"
        session.add(problem)
        session.commit()


@step_router.post(
    "/{step_id}/regenerate",
    response_model=ProblemDraftRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_regeneration(
    project_id: int,
    problem_id: int,
    step_id: int,
    session: SessionDep,
    background_tasks: BackgroundTasks,
) -> Problem:
    step = editable_step(session, project_id, problem_id, step_id)
    problem = step.problem
    if not problem.generation_request:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This draft was generated before its inputs were recorded, "
            "so a single step cannot be reproduced. Generate the problem again.",
        )

    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    restore_status = problem.status
    problem.status = DraftStatus.GENERATING
    session.add(problem)
    session.commit()
    session.refresh(problem)

    background_tasks.add_task(_run_regeneration, step.id, restore_status, _provider_config(project))
    return problem
