from typing import Literal

from pydantic import BaseModel, Field

from app.models import ProblemType


class GenerationRequest(BaseModel):
    topic: str = Field(min_length=3)
    problem_type: ProblemType = ProblemType.TEXT_BOX
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    num_steps: int = Field(default=3, ge=1, le=7)
    num_hints: int = Field(default=1, ge=0, le=7)
    # Off by default so a draft stored before scaffolds existed replays unchanged.
    use_scaffolds: bool = False
    source_document_id: int | None = None
    k: int = Field(default=4, ge=1, le=20)


class ChoiceOption(BaseModel):
    value: str
    label: str
    description: str


class WizardOptions(BaseModel):
    problem_types: list[ChoiceOption]
    difficulties: list[ChoiceOption]


PROBLEM_TYPE_TEXT: dict[ProblemType, tuple[str, str]] = {
    ProblemType.TEXT_BOX: (
        "Text box",
        "Student types an answer — numeric, algebraic, or exact text.",
    ),
    ProblemType.MULTIPLE_CHOICE: ("Multiple choice", "Student picks one of several options."),
    ProblemType.GRID_INPUT: ("Grid", "Student fills a grid of cells, e.g. a table of values."),
    ProblemType.MATRIX_INPUT: ("Matrix", "Student fills a matrix, for linear algebra problems."),
}

DIFFICULTY_TEXT: dict[str, str] = {
    "easy": "Direct application of one idea; suitable right after teaching it.",
    "medium": "Combines a couple of steps or ideas.",
    "hard": "Multi-step reasoning or a less familiar framing.",
}


def wizard_options() -> WizardOptions:
    problem_types = []
    for pt in ProblemType:
        label, description = PROBLEM_TYPE_TEXT[pt]
        problem_types.append(ChoiceOption(value=pt.value, label=label, description=description))
    difficulties = []
    for value, description in DIFFICULTY_TEXT.items():
        difficulties.append(
            ChoiceOption(value=value, label=value.capitalize(), description=description)
        )

    return WizardOptions(problem_types=problem_types, difficulties=difficulties)
