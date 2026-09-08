from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from app.context.derivation import derive_request, derive_slots
from app.context.summary import build_summary
from app.core.db import SessionDep
from app.generation.chains import critique_learning_goal
from app.llm.provider_config import ProviderConfig
from app.models import Project, TutorContext
from app.schemas.context import (
    ContextInput,
    ContextSummaryRead,
    TutorContextRead,
    TutorContextUpdate,
)

router = APIRouter(prefix="/projects/{project_id}/context", tags=["context"])

REQUIRED = {
    "learning_goal": "a learning goal",
    "prior_knowledge": "what learners already know",
    "curricular_placement": "where the tutor sits in your sequence",
    "tutor_roles": "what the tutor is for",
}


def _project(session: SessionDep, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _context(session: SessionDep, project_id: int) -> TutorContext:
    project = _project(session, project_id)
    if project.tutor_context is not None:
        return project.tutor_context
    context = TutorContext(project_id=project_id)
    session.add(context)
    session.commit()
    session.refresh(context)
    return context


def _missing(context: TutorContext) -> list[str]:
    return [label for field, label in REQUIRED.items() if not getattr(context, field)]


@router.get("", response_model=TutorContextRead)
def get_context(project_id: int, session: SessionDep) -> TutorContext:
    return _context(session, project_id)


@router.patch("", response_model=TutorContextRead)
def update_context(project_id: int, payload: TutorContextUpdate, session: SessionDep):
    context = _context(session, project_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(context, field, value)
    context.confirmed_at = None
    context.updated_at = datetime.now(UTC)
    session.add(context)
    session.commit()
    session.refresh(context)
    return context


@router.get("/summary", response_model=ContextSummaryRead)
def get_summary(project_id: int, session: SessionDep) -> ContextSummaryRead:
    """The assembled summary and what it implies"""
    context = _context(session, project_id)
    reading = ContextInput.model_validate(context)
    _, derivations = derive_request(reading)
    slots, slot_derivation = derive_slots(reading)
    return ContextSummaryRead(
        sections=build_summary(reading),
        derivations=[*derivations, slot_derivation],
        num_slots=slots,
        complete=not _missing(context),
        confirmed=context.confirmed_at is not None,
        missing=_missing(context),
    )


@router.post("/confirm", response_model=TutorContextRead)
def confirm_context(project_id: int, session: SessionDep) -> TutorContext:
    context = _context(session, project_id)
    if missing := _missing(context):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Still to answer: {', '.join(missing)}.",
        )
    context.confirmed_at = datetime.now(UTC)
    session.add(context)
    session.commit()
    session.refresh(context)
    return context


@router.post("/critique", response_model=TutorContextRead)
def critique_goal(project_id: int, session: SessionDep) -> TutorContext:
    """Ask the model what is wrong with the learning goal"""
    project = _project(session, project_id)
    context = _context(session, project_id)
    if not context.learning_goal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Write a learning goal first.",
        )

    config = (
        ProviderConfig(provider=project.chat_provider, model=project.chat_model)
        if project.chat_provider
        else None
    )
    try:
        critique = critique_learning_goal(
            learning_goal=context.learning_goal,
            knowledge_type=context.knowledge_type.value,
            prior_knowledge=context.prior_knowledge,
            known_difficulties=context.known_difficulties,
            config=config,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The model could not be reached — {type(exc).__name__}",
        ) from exc

    context.goal_critique = critique.model_dump()
    session.add(context)
    session.commit()
    session.refresh(context)
    return context
