from pydantic import BaseModel, ConfigDict, Field

from app.models import AnswerType, AnswerValidator, ProblemType


class StepCreate(BaseModel):
    oatutor_id: str = Field(pattern=r"^[A-Za-z0-9_]+$")
    order_index: int = 0
    problem_type: ProblemType = ProblemType.TEXT_BOX
    answer_type: AnswerType = AnswerType.STRING
    step_title: str = ""
    step_body: str = ""
    step_answer: list = []
    answer_validator: AnswerValidator = AnswerValidator.DEFAULT
    choices: list[str] | None = None
    num_rows: int | None = None
    num_cols: int | None = None
    skills: list[str] = []


class StepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    problem_id: int
    oatutor_id: str
    order_index: int = 0
    problem_type: ProblemType = ProblemType.TEXT_BOX
    answer_type: AnswerType = AnswerType.STRING
    step_title: str = ""
    step_body: str = ""
    step_answer: list
    answer_validator: AnswerValidator = AnswerValidator.DEFAULT
    choices: list[str] | None = None
    num_rows: int | None = None
    num_cols: int | None = None
    skills: list[str]
