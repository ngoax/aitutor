from pydantic import BaseModel, Field

from app.models import AnswerType, HintType, ProblemType


class HintUpdate(BaseModel):
    """Teacher edits to a generated hint"""

    type: HintType | None = None
    title: str | None = Field(default=None, min_length=1)
    text: str | None = Field(default=None, min_length=1)
    problem_type: ProblemType | None = None
    answer_type: AnswerType | None = None
    hint_answer: list[str] | None = None
    choices: list[str] | None = None
