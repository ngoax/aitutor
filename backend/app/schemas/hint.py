from pydantic import BaseModel, Field

from app.models import HintType


class HintUpdate(BaseModel):
    """Teacher edits to a generated hint"""

    type: HintType | None = None
    title: str | None = Field(default=None, min_length=1)
    text: str | None = Field(default=None, min_length=1)
