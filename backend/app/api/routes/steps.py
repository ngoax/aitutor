from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, select

from app.api.editing import editable_step, mark_edited
from app.core.db import SessionDep
from app.models import Problem, Step
from app.schemas.step import StepCreate, StepRead, StepUpdate

router = APIRouter(prefix="/projects/{project_id}/problems/{problem_id}/steps", tags=["steps"])


def _get_scoped_problem(session: Session, project_id: int, problem_id: int) -> Problem:
    """Fetch a Problem, 404 if missing or doesn't belong to project_id"""
    problem = session.get(Problem, problem_id)
    if problem is None or problem.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    return problem


@router.post("", response_model=StepRead, status_code=status.HTTP_201_CREATED)
def create_step(project_id: int, problem_id: int, payload: StepCreate, session: SessionDep) -> Step:
    _get_scoped_problem(session, project_id, problem_id)
    step = Step(**payload.model_dump(), problem_id=problem_id)
    session.add(step)
    session.commit()
    session.refresh(step)
    return step


@router.get("", response_model=list[StepRead])
def list_steps(project_id: int, problem_id: int, session: SessionDep) -> list[Step]:
    _get_scoped_problem(session, project_id, problem_id)
    return list(
        session.exec(
            select(Step).where(Step.problem_id == problem_id).order_by(Step.order_index)
        ).all()
    )


@router.get("/{step_id}", response_model=StepRead)
def get_step(project_id: int, problem_id: int, step_id: int, session: SessionDep) -> Step:
    _get_scoped_problem(session, project_id, problem_id)
    step = session.get(Step, step_id)
    if step is None or step.problem_id != problem_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step not found")
    return step


@router.patch("/{step_id}", response_model=StepRead)
def update_step(
    project_id: int, problem_id: int, step_id: int, payload: StepUpdate, session: SessionDep
) -> Step:
    step = editable_step(session, project_id, problem_id, step_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(step, field, value)
    step.stale = False
    mark_edited(step.problem)
    session.add(step)
    session.commit()
    session.refresh(step)
    return step


@router.delete("/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_step(project_id: int, problem_id: int, step_id: int, session: SessionDep) -> None:
    _get_scoped_problem(session, project_id, problem_id)
    step = session.get(Step, step_id)
    if step is None or step.problem_id != problem_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step not found")
    session.delete(step)
    session.commit()
