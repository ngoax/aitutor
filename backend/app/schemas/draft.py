from pydantic import BaseModel, ConfigDict

from app.models import HintType
from app.schemas.problem import ProblemRead
from app.schemas.step import StepRead


class HintEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_index: int
    oatutor_id: str
    type: HintType
    title: str
    text: str
    dependencies: list[int]


class StepDraftRead(StepRead):
    hints: list[HintEntryRead]


class ProblemDraftRead(ProblemRead):
    """Generated problem with everything hanging off it, so the review UI can
    render a draft from the single generate response."""

    steps: list[StepDraftRead]
