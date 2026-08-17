from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Request body for creating a project: the fields a client may set"""

    name: str = Field(min_length=1, max_length=200)
    source_name: str = Field(pattern=r"^[A-Za-z0-9_]+$")


class ProjectRead(BaseModel):
    """API response shape for a project"""

    model_config = ConfigDict(from_attributes=True)  # read attributes, not dict keys
    id: int
    name: str
    source_name: str
    created_at: datetime
