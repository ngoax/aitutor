from fastapi import APIRouter

from app.api.editing import editable_hint, mark_edited
from app.core.db import SessionDep
from app.models import HintEntry
from app.schemas.draft import HintEntryRead
from app.schemas.hint import HintUpdate

router = APIRouter(
    prefix="/projects/{project_id}/problems/{problem_id}/steps/{step_id}/hints",
    tags=["hints"],
)


@router.patch("/{hint_id}", response_model=HintEntryRead)
def update_hint(
    project_id: int,
    problem_id: int,
    step_id: int,
    hint_id: int,
    payload: HintUpdate,
    session: SessionDep,
) -> HintEntry:
    hint = editable_hint(session, project_id, problem_id, step_id, hint_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(hint, field, value)
    mark_edited(hint.step.problem)
    session.add(hint)
    session.commit()
    session.refresh(hint)
    return hint
