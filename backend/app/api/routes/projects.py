import shutil

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.core.config import settings
from app.core.db import SessionDep
from app.models import Project
from app.rag.vectorstore import delete_project_index
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, session: SessionDep) -> Project:
    project = Project(name=payload.name, source_name=payload.source_name)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
def list_projects(session: SessionDep) -> list[Project]:
    return list(session.exec(select(Project).order_by(Project.id)).all())


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: SessionDep) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, payload: ProjectUpdate, session: SessionDep) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    # exclude_unset keeps an omitted field untouched, so an explicit null still clears one.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, session: SessionDep) -> None:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    session.delete(project)
    session.commit()
    # Rows cascade, but vectors and uploaded files live outside the database.
    delete_project_index(project_id)
    shutil.rmtree(settings.uploads_dir / str(project_id), ignore_errors=True)
