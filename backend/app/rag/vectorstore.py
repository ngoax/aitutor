import shutil
import threading

import chromadb
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from app.core.config import settings

# chromadb caches one System per persist directory and refcounts it, so holding the
# client here is what lets us release its SQLite handle before deleting the files.
_clients: dict[int, chromadb.ClientAPI] = {}
_clients_lock = threading.Lock()


def _get_client(project_id: int) -> chromadb.ClientAPI:
    with _clients_lock:  # sync routes and background tasks share the threadpool
        client = _clients.get(project_id)
        if client is None:
            persist_directory = settings.chroma_dir / str(project_id)
            persist_directory.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(persist_directory))
            _clients[project_id] = client
        return client


def get_vectorstore(project_id: int, embeddings: Embeddings) -> Chroma:
    return Chroma(
        collection_name=f"project_{project_id}",
        embedding_function=embeddings,
        client=_get_client(project_id),
    )


def delete_document_chunks(project_id: int, embeddings: Embeddings, document_id: int) -> None:
    store = get_vectorstore(project_id, embeddings)
    store.delete(where={"source_document_id": document_id})


def delete_project_index(project_id: int) -> None:
    """Remove a project's whole vector store from disk."""
    with _clients_lock:
        client = _clients.pop(project_id, None)
    if client is not None:
        # Closing releases the open SQLite connection, so a project that later reuses
        # this id does not inherit a handle to the file we are about to delete.
        client.close()
    shutil.rmtree(settings.chroma_dir / str(project_id), ignore_errors=True)
