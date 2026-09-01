import json
from collections import Counter
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, Field, model_validator

from app.models import AnswerType


def _no_control_chars(value: str) -> str:
    """Reject control characters, which can appear via JSON escape corruption"""
    bad = sorted({c for c in value if ord(c) < 32 and c != "\n" or ord(c) == 127})
    if bad:
        codes = ", ".join(hex(ord(c)) for c in bad)
        raise ValueError(
            f"contains control character(s) {codes}. A LaTeX command was written with a "
            r"single backslash; double it (\\frac, \\sqrt, \\times)."
        )
    return value


def _not_serialised_json(value: str) -> str:
    """Reject a field whose whole value is a JSON object.

    Weaker models sometimes answer by serialising an object into a single field
    instead of filling the schema, which passes str validation and lands a blob
    of JSON in front of the teacher.
    """
    stripped = value.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            parsed = json.loads(stripped)
        except ValueError:
            return value
        if isinstance(parsed, dict):
            raise ValueError(
                "contains a serialised JSON object instead of text. Fill each schema "
                "field separately rather than nesting an object inside one of them."
            )
    return value


PromptText = Annotated[str, AfterValidator(_no_control_chars), AfterValidator(_not_serialised_json)]


class GeneratedProblem(BaseModel):
    title: PromptText = Field(
        description=(
            "A short title naming what this specific problem asks. It must tell this "
            "problem apart from others on the same topic, so do not just restate the topic."
        )
    )
    body: PromptText = Field(
        description=(
            "The situation the student reads before answering anything. Give the context "
            "and every value they need. Do not ask a question here and do not work "
            "towards the answer. The steps do that."
        )
    )


class GeneratedStep(BaseModel):
    """Reuse step_title and step_body across problem types"""

    step_title: PromptText = Field(
        description=(
            "A 2-5 word label for what this step asks, e.g. 'Radius of the circle'. "
            "Name the content only. Never refer to the step's position: no 'Step 2', "
            "no 'of 3', no leading number."
        )
    )
    step_body: PromptText = Field(
        description=(
            "The question the student answers in this step. Ask for exactly one value or "
            "expression; the student has a single input box. Assume they have read the "
            "problem body; do not restate the scenario. State only the question: do not "
            "work through it, do not show intermediate results, and do not give the answer. "
            "The student has not solved it yet."
        )
    )

    def answer_text(self) -> str:
        """Force subclasses to implement function to print prompt-friendly formats"""
        raise NotImplementedError


class GeneratedTextBoxStep(GeneratedStep):
    step_answer: list[PromptText] = Field(
        min_length=1,
        description=(
            "Every answer that should be marked correct, as bare values with no "
            "explanation. Each entry is a value the student types, never an instruction "
            "for finding it. Include equivalent forms a student might reasonably type, "
            "such as '0.5' and '1/2'. A 'string' answer is compared literally, so write "
            "those as plain text with no $$."
        ),
    )
    answer_type: AnswerType = Field(
        description=(
            "Use 'arithmetic' for anything mathematical, a plain number included: "
            "OATutor parses it, so equivalent forms are accepted. Use 'string' only when "
            "the answer is a word or a name and must match character for character. "
            "Never use 'numeric'."
        )
    )

    def answer_text(self) -> str:
        return " or ".join(self.step_answer)


class GeneratedMultipleChoiceStep(GeneratedStep):
    choices: list[PromptText] = Field(
        min_length=2,
        description="Generate exactly four different choices. Only ONE can be correct. "
        "The false choices should be plausible and ideally cover common misconceptions",
    )
    step_answer: PromptText = Field(
        min_length=1, description="Entry must match a choice EXACTLY, character for character"
    )

    @model_validator(mode="after")
    def no_duplicate_choices(self) -> Self:
        """Rejects duplicate choices"""
        if len(set(self.choices)) != len(self.choices):
            # https://stackoverflow.com/questions/9835762/how-do-i-find-the-duplicates-in-a-list-and-create-another-list-with-them
            duplicates = [item for item, count in Counter(self.choices).items() if count > 1]
            raise ValueError(f"Choices are not unique. Duplicate elements: {duplicates}")
        return self

    @model_validator(mode="after")
    def answer_must_be_a_choice(self) -> Self:
        """Rejects answer that deviates from the given choices"""
        if self.step_answer not in self.choices:
            raise ValueError(
                f"Answer {self.step_answer} is not a value contained in choices: {self.choices}"
            )
        return self

    def answer_text(self) -> str:
        return self.step_answer


class GeneratedGridStep(GeneratedStep):
    num_rows: int = Field(
        description="Set the number of rows for the grid. "
        "Must be equal to number of entries in rows",
        ge=1,
        le=8,
    )
    num_cols: int = Field(description="Set the number of columns for the grid.", ge=1, le=8)
    rows: list[PromptText] = Field(
        description=(
            "Represent rows with | as the delimiter. For example: 1|2|3 represents a row. "
            "Generate exactly as many rows as num_rows, each with exactly num_cols cells "
            "separated by |."
        )
    )

    def answer_text(self) -> str:
        return "\n".join(self.rows)

    @model_validator(mode="after")
    def rows_match_num_rows(self) -> Self:
        if len(self.rows) != self.num_rows:
            raise ValueError(
                f"Number of rows {len(self.rows)} does not equal value of num_rows: {self.num_rows}"
            )
        return self

    @model_validator(mode="after")
    def row_match_num_cols(self) -> Self:
        for pos, row in enumerate(self.rows):
            cells = row.split("|")
            if len(cells) != self.num_cols:
                raise ValueError(
                    f"Row {pos} ({row}) has {len(cells)} columns but num_cols is {self.num_cols}"
                )
        return self


class GeneratedHint(BaseModel):
    title: PromptText = Field(
        description=(
            "A 2-5 word label for what this hint addresses, e.g. 'Which numbers multiply "
            "to 24'. Do not add a leading number."
        )
    )
    text: PromptText = Field(
        description=(
            "What the student reads when they open this hint. Address them directly and "
            "keep it to one or two sentences."
        )
    )


class GeneratedHintPathway(BaseModel):
    hints: list[GeneratedHint] = Field(
        min_length=1,
        description=(
            "An ordered sequence a stuck student works through, each one revealing more "
            "than the last. The first points at the idea this step depends on without doing "
            "any of the work. Middle hints narrow it down one move at a time. The final hint "
            "states the answer and explains why it follows. Never repeat what an earlier "
            "hint already gave away."
        ),
    )
