from langchain_xberg import XbergLoader
from xberg import ChunkerType, ChunkingConfig, ExtractionConfig, LayoutDetectionConfig

from app.models import SourceDocument
from app.rag.embeddings import get_embedding_model
from app.rag.vectorstore import delete_document_chunks, get_vectorstore


def ingest_document(document: SourceDocument) -> int:
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
    get_vectorstore(document.project_id, embeddings).add_documents(docs)
    return len(docs)
