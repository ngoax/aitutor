from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import DraftStatus


class ProblemCreate(BaseModel):
    oatutor_id: str = Field(pattern=r"^[A-Za-z0-9_]+$")
    title: str
    body: str = ""
    course_name: str = ""
    oer: str | None = None
    topic: str | None = None
    difficulty: str | None = None


class ProblemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    oatutor_id: str
    title: str
    body: str
    course_name: str
    oer: str | None = None
    topic: str | None = None
    difficulty: str | None = None
    status: DraftStatus
    created_at: datetime
