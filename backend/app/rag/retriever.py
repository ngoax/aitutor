from langchain_core.documents import Document

from app.rag.embeddings import get_embedding_model
from app.rag.vectorstore import get_vectorstore


def retrieve(
    project_id: int, query: str, k: int = 4, source_document_id: int | None = None
) -> list[Document]:
    embedding = get_embedding_model()
    vector_store = get_vectorstore(project_id=project_id, embeddings=embedding)
    filter = None
    if source_document_id is not None:
        filter = {"source_document_id": source_document_id}
    return vector_store.similarity_search(query, k=k, filter=filter)
