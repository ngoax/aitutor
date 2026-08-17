import shutil

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from app.core.config import settings


def get_vectorstore(project_id: int, embeddings: Embeddings) -> Chroma:
    persist_directory = settings.chroma_dir / str(project_id)
    persist_directory.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=f"project_{project_id}",
        embedding_function=embeddings,
        persist_directory=str(persist_directory),
    )


def delete_document_chunks(project_id: int, embeddings: Embeddings, document_id: int) -> None:
    store = get_vectorstore(project_id, embeddings)
    store.delete(where={"source_document_id": document_id})


def delete_project_index(project_id: int) -> None:
    """Remove a project's whole vector store from disk."""
    shutil.rmtree(settings.chroma_dir / str(project_id), ignore_errors=True)
