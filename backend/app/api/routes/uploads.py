import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import SessionDep, engine
from app.models import IngestionStatus, Project, SourceDocument
from app.rag.embeddings import get_embedding_model
from app.rag.ingest import ingest_document
from app.rag.vectorstore import delete_document_chunks
from app.schemas.document import SourceDocumentRead

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


def _get_project_or_404(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _run_ingestion(document_id: int) -> None:
    """Runs after the response is sent, so it needs a session of its own."""
    with Session(engine) as session:
        document = session.get(SourceDocument, document_id)
        if document is None:
            return
        try:
            chunk_count = ingest_document(document)
            document.status = IngestionStatus.INDEXED
            document.chunk_count = chunk_count
            document.error = None
        except Exception as exc:  # surfaced to the teacher via GET /documents
            document.status = IngestionStatus.FAILED
            document.error = f"{type(exc).__name__}: {exc}"
        session.add(document)
        session.commit()


@router.post("", response_model=SourceDocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    project_id: int,
    session: SessionDep,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
) -> SourceDocument:
    _get_project_or_404(session, project_id)

    original_name = Path(file.filename or "upload").name
    destination_dir = settings.uploads_dir / str(project_id)
    destination_dir.mkdir(parents=True, exist_ok=True)
    # Uuid prefix keeps two uploads of the same filename from overwriting each other
    stored_path = destination_dir / f"{uuid.uuid4().hex}_{original_name}"
    stored_path.write_bytes(file.file.read())

    document = SourceDocument(
        project_id=project_id,
        filename=original_name,
        stored_path=str(stored_path),
        content_type=file.content_type,
        status=IngestionStatus.PENDING,
    )
    session.add(document)
    session.commit()
    session.refresh(document)

    # Layout detection and OCR are far too slow to hold response open
    background_tasks.add_task(_run_ingestion, document.id)
    return document


@router.get("", response_model=list[SourceDocumentRead])
def list_documents(project_id: int, session: SessionDep) -> list[SourceDocument]:
    _get_project_or_404(session, project_id)
    statement = (
        select(SourceDocument)
        .where(SourceDocument.project_id == project_id)
        .order_by(SourceDocument.id)
    )
    return list(session.exec(statement).all())


@router.get("/{document_id}", response_model=SourceDocumentRead)
def get_document(project_id: int, document_id: int, session: SessionDep) -> SourceDocument:
    document = session.get(SourceDocument, document_id)
    if document is None or document.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(project_id: int, document_id: int, session: SessionDep) -> None:
    document = session.get(SourceDocument, document_id)
    if document is None or document.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    delete_document_chunks(project_id, get_embedding_model(), document_id)
    Path(document.stored_path).unlink(missing_ok=True)
    session.delete(document)
    session.commit()
