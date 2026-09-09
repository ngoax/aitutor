from collections.abc import Callable

from langchain_xberg import XbergLoader
from xberg import ChunkerType, ChunkingConfig, ExtractionConfig, LayoutDetectionConfig

from app.models import SourceDocument
from app.rag.embeddings import get_embedding_model
from app.rag.vectorstore import delete_document_chunks, get_vectorstore

# Chunks per embedding call. Small enough that progress moves visibly, large
# enough that the per-call overhead stays negligible.
BATCH_SIZE = 8


def ingest_document(
    document: SourceDocument,
    on_progress: Callable[[int, int], None] | None = None,
) -> int:
    """Load, chunk, embed and index one uploaded document"""
    config = ExtractionConfig(
        output_format="markdown",
        include_document_structure=True,
        use_layout_for_markdown=True,
        layout=LayoutDetectionConfig(strategy="always"),
        chunking=ChunkingConfig(
            max_characters=1000,
            overlap=200,
            chunker_type=ChunkerType.MARKDOWN,
            prepend_heading_context=True,
        ),
    )

    docs = XbergLoader(file_path=document.stored_path, config=config).load()

    embeddings = get_embedding_model()
    delete_document_chunks(
        document.project_id, embeddings, document.id
    )  # delete old chunks to prevent duplicates for same document
    for chunk in docs:
        # convert metadata into scalars for ChromaDB
        chunk.metadata = {
            k: v
            for k, v in chunk.metadata.items()
            if v is None or isinstance(v, (str, int, float, bool))
        }
        chunk.metadata["source_document_id"] = document.id  # Assign source document to each chunk

    store = get_vectorstore(document.project_id, embeddings)
    if on_progress is not None:
        on_progress(0, len(docs))
    for start in range(0, len(docs), BATCH_SIZE):
        store.add_documents(docs[start : start + BATCH_SIZE])
        if on_progress is not None:
            on_progress(min(start + BATCH_SIZE, len(docs)), len(docs))
    return len(docs)
