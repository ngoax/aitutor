"""Pydantic mirror of the JSON OATutor actually reads.

Field sets and optionality come from all 17761 steps in CAHLR/OATutor-Content;
`extra="forbid"` so a key we invent fails here rather than in the tutor.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.models import AnswerType, ProblemType

# OATutor's renderer branches on "scaffold" and "gptHint" only. Our own
# `solution` marks the entry that gives the answer away and has to map to "hint".
ExportHintType = Literal["hint", "scaffold"]


class OATutorModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ProblemJson(OATutorModel):
    """content-pool/<id>/<id>.json"""

    id: str
    title: str
    body: str = ""
    variabilization: dict[str, Any] = Field(default_factory=dict)
    oer: str = ""
    license: str = ""
    lesson: str = ""
    lesson_id: str = ""
    course_name: str = ""


class StepJson(OATutorModel):
    """content-pool/<id>/steps/<stepId>/<stepId>.json"""

    id: str
    step_answer: list[str] = Field(min_length=1)
    problem_type: ProblemType
    answer_type: AnswerType
    step_title: str
    step_body: str = ""
    variabilization: dict[str, Any] = Field(default_factory=dict)
    # Display form of the answer, separate from the graded step_answer.
    answer_latex: str | None = None
    choices: list[str] | None = None
    # GridInput reads these straight off the step.
    num_rows: int | None = None
    num_cols: int | None = None


class HintJson(OATutorModel):
    """One entry in steps/<stepId>/tutoring/<stepId>DefaultPathway.json"""

    id: str
    type: ExportHintType
    title: str
    text: str
    # Ids of earlier entries, not indices.
    dependencies: list[str] = Field(default_factory=list)
    variabilization: dict[str, Any] = Field(default_factory=dict)
    oer: str = ""
    license: str = ""
    # A scaffold is a mini problem with its own input, so it carries these too.
    problem_type: ProblemType | None = None
    answer_type: AnswerType | None = None
    hint_answer: list[str] | None = None
    choices: list[str] | None = None
    sub_hints: list["HintJson"] | None = None
