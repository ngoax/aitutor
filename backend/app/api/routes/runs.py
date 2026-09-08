from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlmodel import Session, select

from app.context.derivation import derive_request, derive_slots
from app.core.db import SessionDep, engine
from app.generation.persist import persist_alternative
from app.generation.pipeline import generate_alternatives
from app.llm.provider_config import ProviderConfig
from app.models import GenerationRun, Problem, Project, RunStatus
from app.schemas.context import ContextInput
from app.schemas.generation import GenerationRequest
from app.schemas.run import RunCreate, RunDetailRead, RunRead, SlotRead

router = APIRouter(prefix="/projects/{project_id}/runs", tags=["runs"])


def _run_generation(run_id: int, config: ProviderConfig | None) -> None:
    with Session(engine) as session:
        run = session.get(GenerationRun, run_id)
        if run is None:
            return
        request = GenerationRequest(**run.request_snapshot)
        try:
            for slot in range(run.num_slots):
                drafts = generate_alternatives(
                    request=request,
                    project_id=run.project_id,
                    count=run.num_alternatives,
                    config=config,
                )
                for index, draft in enumerate(drafts):
                    persist_alternative(session, run, slot, index, request, draft)
            run.status = RunStatus.READY
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = f"{type(exc).__name__}: {exc}"
        session.add(run)
        session.commit()


@router.post("", response_model=RunRead, status_code=status.HTTP_202_ACCEPTED)
def start_run(
    project_id: int,
    payload: RunCreate,
    session: SessionDep,
    background_tasks: BackgroundTasks,
) -> GenerationRun:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    context = project.tutor_context
    if context is None or context.confirmed_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Confirm the context summary before generating.",
        )

    reading = ContextInput.model_validate(context)
    request, _ = derive_request(reading)
    slots, _ = derive_slots(reading)

    run = GenerationRun(
        project_id=project_id,
        context_snapshot=reading.model_dump(mode="json"),
        request_snapshot=request.model_dump(mode="json"),
        num_slots=payload.num_slots or slots,
        num_alternatives=payload.num_alternatives,
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    config = (
        ProviderConfig(provider=project.chat_provider, model=project.chat_model)
        if project.chat_provider
        else None
    )
    background_tasks.add_task(_run_generation, run.id, config)
    return run


@router.get("", response_model=list[RunRead])
def list_runs(project_id: int, session: SessionDep) -> list[GenerationRun]:
    return list(
        session.exec(
            select(GenerationRun)
            .where(GenerationRun.project_id == project_id)
            .order_by(GenerationRun.id.desc())
        ).all()
    )


@router.get("/{run_id}", response_model=RunDetailRead)
def get_run(project_id: int, run_id: int, session: SessionDep) -> RunDetailRead:
    run = session.get(GenerationRun, run_id)
    if run is None or run.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    problems = session.exec(
        select(Problem)
        .where(Problem.run_id == run_id)
        .order_by(Problem.slot_index, Problem.alternative_index)
    ).all()

    slots: dict[int, list[Problem]] = {}
    for problem in problems:
        slots.setdefault(problem.slot_index, []).append(problem)

    return RunDetailRead(
        **RunRead.model_validate(run).model_dump(),
        slots=[SlotRead(slot_index=i, alternatives=slots[i]) for i in sorted(slots)],
    )
