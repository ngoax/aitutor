"""Lookups shared by the endpoints that let a teacher edit a generated draft."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import DraftStatus, HintEntry, Problem, Step


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


def editable_problem(session: Session, project_id: int, problem_id: int) -> Problem:
    problem = session.get(Problem, problem_id)
    if problem is None or problem.project_id != project_id:
        raise _not_found("Problem")
    if problem.status is DraftStatus.GENERATING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This draft is still generating. Wait for it to finish before editing.",
        )
    return problem


def editable_step(session: Session, project_id: int, problem_id: int, step_id: int) -> Step:
    problem = editable_problem(session, project_id, problem_id)
    step = session.get(Step, step_id)
    if step is None or step.problem_id != problem.id:
        raise _not_found("Step")
    return step


def editable_hint(
    session: Session, project_id: int, problem_id: int, step_id: int, hint_id: int
) -> HintEntry:
    step = editable_step(session, project_id, problem_id, step_id)
    hint = session.get(HintEntry, hint_id)
    if hint is None or hint.step_id != step.id:
        raise _not_found("Hint")
    return hint


def mark_edited(problem: Problem) -> None:
    problem.status = DraftStatus.EDITED
    problem.error = None
