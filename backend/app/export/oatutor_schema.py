"""Pydantic mirror of the JSON OATutor actually reads."""

from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator
from pydantic.alias_generators import to_camel

from app.models import AnswerType, ProblemType

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
    answer_latex: str | None = None
    choices: list[str] | None = None
    num_rows: int | None = None
    num_cols: int | None = None

    @model_validator(mode="after")
    def answers_must_be_choices(self) -> Self:
        if self.problem_type is not ProblemType.MULTIPLE_CHOICE:
            return self
        if self.choices is None or len(self.choices) < 2:
            raise ValueError(f"MultipleChoice needs at least two choices, got {self.choices}")
        missing = [answer for answer in self.step_answer if answer not in self.choices]
        if missing:
            raise ValueError(f"Answers {missing} are not among the choices {self.choices}")
        return self

    @model_validator(mode="after")
    def grid_needs_dimensions(self) -> Self:
        dimensions = {"numRows": self.num_rows, "numCols": self.num_cols}
        if self.problem_type is ProblemType.GRID_INPUT:
            absent = [name for name, value in dimensions.items() if value is None]
            if absent:
                raise ValueError(f"GridInput step {self.id} is missing {', '.join(absent)}")
        else:
            present = [name for name, value in dimensions.items() if value is not None]
            if present:
                raise ValueError(f"{self.problem_type} must not set {', '.join(present)}")
        return self


class HintJson(OATutorModel):
    """One entry in steps/<stepId>/tutoring/<stepId>DefaultPathway.json"""

    id: str
    type: ExportHintType
    title: str
    text: str
    dependencies: list[str] = Field(default_factory=list)
    variabilization: dict[str, Any] = Field(default_factory=dict)
    oer: str = ""
    license: str = ""
    problem_type: ProblemType | None = None
    answer_type: AnswerType | None = None
    hint_answer: list[str] | None = None
    choices: list[str] | None = None
    sub_hints: list["HintJson"] | None = None

    @model_validator(mode="after")
    def scaffold_fields_match_type(self) -> Self:
        answerable = {
            "problemType": self.problem_type,
            "answerType": self.answer_type,
            "hintAnswer": self.hint_answer,
        }
        if self.type == "scaffold":
            absent = [name for name, value in answerable.items() if value is None]
            if absent:
                raise ValueError(f"Scaffold {self.id} is missing {', '.join(absent)}")
        else:
            present = [name for name, value in answerable.items() if value is not None]
            if present:
                raise ValueError(f"Hint {self.id} must not set {', '.join(present)}")
        return self


class HintPathwayJson(RootModel[list[HintJson]]):
    """steps/<stepId>/tutoring/<stepId>DefaultPathway.json"""

    @model_validator(mode="after")
    def dependencies_point_backwards(self) -> Self:
        """Every id in an entry's dependencies must belong to an entry earlier"""
        seen: set[str] = set()
        for entry in self.root:
            unknown = [name for name in entry.dependencies if name not in seen]
            if unknown:
                raise ValueError(f"{entry.id} depends on {unknown}, which do not come before it")
            seen.add(entry.id)
        return self
