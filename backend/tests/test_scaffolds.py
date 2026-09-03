"""Scaffolds from generated schema through to the exported pathway file."""

import pytest
from pydantic import ValidationError

from app.export.exporter import _pathway_json
from app.export.oatutor_schema import HintPathwayJson
from app.generation.output_schemas import (
    GeneratedChoiceScaffold,
    GeneratedHint,
    GeneratedHintPathway,
    GeneratedScaffoldPathway,
    GeneratedTextBoxScaffold,
)
from app.generation.persist import add_hints
from app.models import AnswerType, HintType, ProblemType

LICENSE = "https://creativecommons.org/licenses/by/4.0/ <CC BY 4.0>"

OPENER = {"title": "What a and c are", "text": "Look at the first and last coefficients."}
TEXT_SCAFFOLD = {
    "kind": "textbox_scaffold",
    "title": "Multiply them",
    "text": "What is $$6 \\times 2$$?",
    "hint_answer": "$$12$$",
    "answer_type": "arithmetic",
}
CHOICE_SCAFFOLD = {
    "kind": "choice_scaffold",
    "title": "Pick the pair",
    "text": "Which pair multiplies to 12 and adds to 13?",
    "hint_answer": "1 and 12",
    "choices": ["1 and 12", "2 and 6", "3 and 4", "12 and 13"],
}
CLOSER = {"title": "The product", "text": "It is $$12$$, because $$6 \\times 2 = 12$$."}


def test_kind_selects_the_shape():
    pathway = GeneratedScaffoldPathway.model_validate(
        {"hints": [OPENER, TEXT_SCAFFOLD, CHOICE_SCAFFOLD, CLOSER]}
    )
    assert [type(entry) for entry in pathway.hints] == [
        GeneratedHint,
        GeneratedTextBoxScaffold,
        GeneratedChoiceScaffold,
        GeneratedHint,
    ]


def test_scaffolds_are_unavailable_without_them():
    """Turning scaffolds off removes the shape from the schema, so a model that
    writes one anyway is rejected rather than silently flattened."""
    with pytest.raises(ValidationError):
        GeneratedHintPathway.model_validate({"hints": [OPENER, TEXT_SCAFFOLD, CLOSER]})


def test_pathway_may_not_end_on_a_question():
    with pytest.raises(ValidationError, match="last entry"):
        GeneratedScaffoldPathway.model_validate({"hints": [OPENER, TEXT_SCAFFOLD]})


def test_choice_scaffold_answer_must_be_a_choice():
    with pytest.raises(ValidationError, match="not a value contained in choices"):
        GeneratedChoiceScaffold.model_validate(CHOICE_SCAFFOLD | {"hint_answer": "5 and 7"})


def test_persisted_columns_match_the_shape(session, step):
    pathway = GeneratedScaffoldPathway.model_validate(
        {"hints": [OPENER, TEXT_SCAFFOLD, CHOICE_SCAFFOLD, CLOSER]}
    )
    add_hints(session, step, pathway.hints)
    session.commit()
    session.refresh(step)

    opener, text, choice, closer = sorted(step.hints, key=lambda hint: hint.order_index)

    assert opener.type is HintType.HINT
    assert opener.hint_answer is None

    assert text.type is HintType.SCAFFOLD
    assert text.problem_type is ProblemType.TEXT_BOX
    assert text.answer_type is AnswerType.ARITHMETIC
    # A list because that is the shape OATutor reads, and it is always one entry.
    assert text.hint_answer == ["$$12$$"]
    assert text.choices is None

    assert choice.problem_type is ProblemType.MULTIPLE_CHOICE
    assert choice.answer_type is AnswerType.STRING
    assert choice.choices == CHOICE_SCAFFOLD["choices"]

    # Ours, not OATutor's: the exporter maps it back down to "hint".
    assert closer.type is HintType.SOLUTION
    assert [hint.oatutor_id for hint in step.hints] == [
        f"{step.oatutor_id}-h{n}" for n in range(1, 5)
    ]


def test_export_produces_a_valid_pathway(session, step):
    pathway = GeneratedScaffoldPathway.model_validate(
        {"hints": [OPENER, TEXT_SCAFFOLD, CHOICE_SCAFFOLD, CLOSER]}
    )
    add_hints(session, step, pathway.hints)
    session.commit()
    session.refresh(step)

    entries = HintPathwayJson(_pathway_json(step, LICENSE)).root

    assert [entry.type for entry in entries] == ["hint", "scaffold", "scaffold", "hint"]
    assert entries[2].choices == CHOICE_SCAFFOLD["choices"]
    assert entries[3].hint_answer is None
    # Written as ids, not indices, and each one has to name the entry before it.
    assert [entry.dependencies for entry in entries] == [
        [],
        [entries[0].id],
        [entries[1].id],
        [entries[2].id],
    ]


def test_scaffold_without_an_answer_is_rejected(session, step):
    pathway = GeneratedScaffoldPathway.model_validate({"hints": [OPENER, TEXT_SCAFFOLD, CLOSER]})
    add_hints(session, step, pathway.hints)
    session.commit()
    session.refresh(step)
    step.hints[1].hint_answer = []
    session.commit()

    with pytest.raises(ValidationError, match="hintAnswer"):
        HintPathwayJson(_pathway_json(step, LICENSE))


@pytest.mark.parametrize(
    "field",
    [
        {"text": "The model is \\(y = mx + b\\), a straight line."},
        {"title": "Solve \\[x^2 = 9\\]"},
    ],
)
def test_delimiters_oatutor_ignores_are_rejected(session, step, field):
    add_hints(session, step, GeneratedHintPathway.model_validate({"hints": [OPENER]}).hints)
    session.commit()
    for key, value in field.items():
        setattr(step.hints[0], key, value)
    session.commit()

    with pytest.raises(ValueError, match="plain text"):
        _pathway_json(step, LICENSE)


def test_scaffold_answer_may_not_carry_them_either(session, step):
    """A scaffold answer is graded, so KAS would never parse it."""
    pathway = GeneratedScaffoldPathway.model_validate({"hints": [OPENER, TEXT_SCAFFOLD, CLOSER]})
    add_hints(session, step, pathway.hints)
    session.commit()
    step.hints[1].hint_answer = ["\\(12\\)"]
    session.commit()

    with pytest.raises(ValueError, match="hintAnswer"):
        _pathway_json(step, LICENSE)


def test_real_latex_survives(session, step):
    pathway = GeneratedScaffoldPathway.model_validate(
        {
            "hints": [
                OPENER,
                TEXT_SCAFFOLD | {"hint_answer": "$$\\left(\\frac{1}{2}\\right)$$"},
                CLOSER,
            ]
        }
    )
    add_hints(session, step, pathway.hints)
    session.commit()

    entries = _pathway_json(step, LICENSE)
    assert entries[1].hint_answer == ["$$\\left(\\frac{1}{2}\\right)$$"]
