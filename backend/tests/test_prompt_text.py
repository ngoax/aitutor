"""Guards on generated text, which the retry loop feeds back to the model."""

import pytest
from pydantic import BaseModel, ValidationError

from app.generation.output_schemas import GeneratedTextBoxStep, PromptText


class Sample(BaseModel):
    value: PromptText


@pytest.mark.parametrize(
    "value",
    [
        "Factor the Quadratic $8x^2+14x+3$",  # the delimiter OATutor ignores
        "Understanding $h(x)$",
        "It costs $36 in total.",  # unescaped, so indistinguishable from a delimiter
    ],
)
def test_single_dollar_is_rejected(value):
    with pytest.raises(ValidationError, match="single"):
        Sample(value=value)


@pytest.mark.parametrize(
    "value",
    [
        "Factor the quadratic $$8x^2+14x+3$$.",
        "The value is $$\\frac{1}{2}$$ exactly.",
        "It costs \\$36 in total.",
        "No maths here at all.",
        "Two spans: $$a$$ and $$b$$.",
    ],
)
def test_correct_forms_pass(value):
    assert Sample(value=value).value == value


@pytest.mark.parametrize(
    ("answer_type", "answers"),
    [
        ("arithmetic", ["$$-9,8$$"]),
        ("arithmetic", ["$$12$$", "$$8,-9$$"]),
    ],
)
def test_arithmetic_answers_may_not_hold_a_comma(answer_type, answers):
    with pytest.raises(ValidationError, match="comma"):
        GeneratedTextBoxStep(
            step_title="Find the pair",
            step_body="Which two integers multiply to $$-72$$?",
            step_answer=answers,
            answer_type=answer_type,
        )


def test_a_list_answer_is_fine_as_a_string():
    step = GeneratedTextBoxStep(
        step_title="Find the pair",
        step_body="Which two integers multiply to $$-72$$?",
        step_answer=["-9,8", "8,-9"],
        answer_type="string",
    )
    assert step.answer_type == "string"
