from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    text: str = ""
    citation_page: int | None = None
    source_document_id: int | None = None
    chunk_index: int | None = None
