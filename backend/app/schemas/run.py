from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import RunStatus
from app.schemas.draft import ProblemDraftRead


class RunCreate(BaseModel):
    # Defaults to what the context implies; the teacher may ask for fewer or more.
    num_slots: int | None = Field(default=None, ge=1, le=20)
    num_alternatives: int = Field(default=3, ge=2, le=5)


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    num_slots: int
    num_alternatives: int
    status: RunStatus
    error: str | None = None
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    request_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SlotRead(BaseModel):
    """One task slot with the candidates written for it."""

    slot_index: int
    alternatives: list[ProblemDraftRead]


class RunDetailRead(RunRead):
    slots: list[SlotRead]
