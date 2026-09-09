from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import IngestionStatus


class SourceDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    filename: str
    content_type: str | None
    status: IngestionStatus
    chunk_count: int
    error: str | None
    progress_done: int = 0
    progress_total: int = 0
    created_at: datetime
