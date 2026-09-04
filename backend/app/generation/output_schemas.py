import json
from collections import Counter
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, Field, model_validator

from app.export.markdown_utils import comma_answers, dollar_wrapped, has_stray_dollar
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
    """Reject a field whose whole value is a JSON object"""
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


def _no_stray_dollar(value: str) -> str:
    if has_stray_dollar(value):
        raise ValueError(
            "uses a single $ where OATutor only recognises $$, so it would be printed "
            r"literally. Wrap maths in $$, and write a dollar sign as \$."
        )
    return value


PromptText = Annotated[
    str,
    AfterValidator(_no_control_chars),
    AfterValidator(_not_serialised_json),
    AfterValidator(_no_stray_dollar),
]


def check_choices(choices: list[str], answer: str) -> None:
    if len(set(choices)) != len(choices):
        # https://stackoverflow.com/questions/9835762/how-do-i-find-the-duplicates-in-a-list-and-create-another-list-with-them
        duplicates = [item for item, count in Counter(choices).items() if count > 1]
        raise ValueError(f"Choices are not unique. Duplicate elements: {duplicates}")
    if answer not in choices:
        raise ValueError(f"Answer {answer} is not a value contained in choices: {choices}")


def check_typed_answers(answer_type: AnswerType, answers: list[str]) -> None:
    if answer_type is AnswerType.ARITHMETIC and (commas := comma_answers(answers)):
        raise ValueError(
            f"Arithmetic answers {commas} contain a comma, which OATutor's parser "
            "rejects, so the step could never be answered. Ask for a single value "
            "instead, or use 'string' if the answer really is a list."
        )
    if answer_type is AnswerType.STRING and (wrapped := dollar_wrapped(answers)):
        raise ValueError(
            f"String answers {wrapped} are wrapped in $$, which is compared literally "
            "rather than stripped, so the student would have to type the $$ too. "
            "Write a string answer bare."
        )


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
            "Never use 'numeric'. The parser rejects commas, so an answer containing "
            "one must be 'string' rather than 'arithmetic'."
        )
    )

    @model_validator(mode="after")
    def answers_must_be_enterable(self) -> Self:
        check_typed_answers(self.answer_type, self.step_answer)
        return self

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
    def answer_must_be_a_choice(self) -> Self:
        check_choices(self.choices, self.step_answer)
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
    """An entry the student reads and moves on from."""

    kind: Literal["hint"] = "hint"
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


class GeneratedScaffold(GeneratedHint):
    """An entry the student has to answer before moving on."""

    text: PromptText = Field(
        description=(
            "The question the student answers here. Ask for one intermediate value on the "
            "way to the step's answer, never the step's answer itself. Address them "
            "directly and keep it to one or two sentences."
        )
    )
    hint_answer: PromptText = Field(
        min_length=1,
        description=(
            "The answer to the question above, as a bare value with no explanation. It is "
            "graded against what the student types, so write only what they should enter."
        ),
    )


class GeneratedTextBoxScaffold(GeneratedScaffold):
    """A scaffold the student answers by typing."""

    kind: Literal["textbox_scaffold"] = "textbox_scaffold"
    answer_type: AnswerType = Field(
        description=(
            "Use 'arithmetic' for anything mathematical, a plain number included. Use "
            "'string' only when the answer is a word or a name and must match character "
            "for character, and write those bare, with no $$. Never use 'numeric'."
        )
    )

    @model_validator(mode="after")
    def answer_must_be_enterable(self) -> Self:
        check_typed_answers(self.answer_type, [self.hint_answer])
        return self


class GeneratedChoiceScaffold(GeneratedScaffold):
    """A scaffold the student answers by picking one of several options."""

    kind: Literal["choice_scaffold"] = "choice_scaffold"
    choices: list[PromptText] = Field(
        min_length=2,
        description=(
            "Generate exactly four different choices. Only ONE can be correct. The false "
            "choices should be plausible and ideally cover common misconceptions."
        ),
    )

    @model_validator(mode="after")
    def answer_must_be_a_choice(self) -> Self:
        check_choices(self.choices, self.hint_answer)
        return self


PATHWAY_DESCRIPTION = (
    "An ordered sequence a stuck student works through, each one revealing more "
    "than the last. The first points at the idea this step depends on without doing "
    "any of the work. Middle entries narrow it down one move at a time. The final one "
    "states the answer and explains why it follows, so it must be a plain hint and not "
    "a question. Never repeat what an earlier entry already gave away."
)

SCAFFOLD_DESCRIPTION = (
    " Where a middle entry would otherwise hand over an intermediate value, ask the "
    "student for it instead: write a scaffold, which is a question they answer inside "
    "the hint. Only use one where answering is genuinely the next move a tutor would "
    "ask for, and never for the step's own answer."
)


class GeneratedHintPathway(BaseModel):
    hints: list[GeneratedHint] = Field(min_length=1, description=PATHWAY_DESCRIPTION)

    @model_validator(mode="after")
    def ends_with_the_answer(self) -> Self:
        """A stuck student must always reach the answer, so the pathway cannot end
        on a question."""
        if isinstance(self.hints[-1], GeneratedScaffold):
            raise ValueError(
                "The last entry must be a plain hint stating the answer, not a scaffold "
                "asking for it."
            )
        return self


class GeneratedScaffoldPathway(GeneratedHintPathway):
    hints: list[GeneratedHint | GeneratedTextBoxScaffold | GeneratedChoiceScaffold] = Field(
        min_length=1, description=PATHWAY_DESCRIPTION + SCAFFOLD_DESCRIPTION
    )
