from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.editing import editable_problem, mark_edited
from app.core.db import SessionDep
from app.models import Problem, Project
from app.schemas.problem import ProblemCreate, ProblemRead, ProblemUpdate

router = APIRouter(prefix="/projects/{project_id}/problems", tags=["problems"])


@router.post("", response_model=ProblemRead, status_code=201)
def create_problem(project_id: int, payload: ProblemCreate, session: SessionDep) -> Problem:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    problem = Problem(**payload.model_dump(), project_id=project_id)
    session.add(problem)
    session.commit()
    session.refresh(problem)
    return problem


@router.get("", response_model=list[ProblemRead])
def list_problems(session: SessionDep, project_id: int) -> list[Problem]:
    statement = select(Problem).where(Problem.project_id == project_id).order_by(Problem.id)
    return list(session.exec(statement).all())


@router.get("/{problem_id}", response_model=ProblemRead)
def get_problem(project_id: int, problem_id: int, session: SessionDep) -> Problem:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    problem = session.get(Problem, problem_id)
    if problem is None or problem.project_id != project_id:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.patch("/{problem_id}", response_model=ProblemRead)
def update_problem(
    project_id: int, problem_id: int, payload: ProblemUpdate, session: SessionDep
) -> Problem:
    problem = editable_problem(session, project_id, problem_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(problem, field, value)
    mark_edited(problem)
    session.add(problem)
    session.commit()
    session.refresh(problem)
    return problem


@router.delete("/{problem_id}", status_code=204)
def delete_problem(project_id: int, problem_id: int, session: SessionDep) -> None:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    problem = session.get(Problem, problem_id)
    if problem is None or problem.project_id != project_id:
        raise HTTPException(status_code=404, detail="Problem not found")
    session.delete(problem)
    session.commit()
