from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.llm.provider_config import ChatProvider


class ProjectCreate(BaseModel):
    """Request body for creating a project: the fields a client may set"""

    name: str = Field(min_length=1, max_length=200)
    source_name: str = Field(pattern=r"^[A-Za-z0-9_]+$")


class ProjectUpdate(BaseModel):
    """Partial update with source_name excluded since changing it would oprhan anything written"""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    license: str | None = None
    chat_provider: ChatProvider | None = None
    chat_model: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None


class ProjectRead(BaseModel):
    """API response shape for a project"""

    model_config = ConfigDict(from_attributes=True)  # read attributes, not dict keys
    id: int
    name: str
    source_name: str
    license: str = ""
    chat_provider: str | None = None
    chat_model: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    created_at: datetime
