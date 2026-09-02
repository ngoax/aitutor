from fastapi import APIRouter, HTTPException, status

from app.core.db import SessionDep
from app.export.exporter import ExportResult, export_project
from app.models import Project

router = APIRouter(prefix="/projects/{project_id}/export", tags=["export"])


@router.post("", response_model=ExportResult)
def export(project_id: int, session: SessionDep) -> ExportResult:
    """Write every exportable problem and report the ones that were not."""
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return export_project(session, project)
