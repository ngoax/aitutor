from fastapi import APIRouter, HTTPException

from app.core.db import SessionDep
from app.models import Project
from app.rag.retriever import retrieve
from app.schemas.retrieval import RetrievedChunk

router = APIRouter(prefix="/projects/{project_id}/retrieval", tags=["retrieval"])


@router.get("/test", response_model=list[RetrievedChunk])
def test_retrieval(
    project_id: int,
    query: str,
    session: SessionDep,
    k: int = 4,
    source_document_id: int | None = None,
) -> list[RetrievedChunk]:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    docs = retrieve(project_id=project_id, query=query, k=k, source_document_id=source_document_id)
    return [
        RetrievedChunk(
            text=doc.page_content,
            citation_page=doc.metadata.get("page"),
            source_document_id=doc.metadata.get("source_document_id"),
            chunk_index=doc.metadata.get("chunk_index"),
        )
        for doc in docs
    ]
