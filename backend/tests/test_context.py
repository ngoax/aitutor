"""Contextualization: the context has to change the tutor, or it is busywork."""

import pytest

from app.context.derivation import KNOWLEDGE_PATTERNS, derive_request, derive_slots
from app.context.summary import build_summary, summary_text
from app.generation.prompts import PROBLEM_PROMPT, format_teaching_context
from app.models import FeedbackMode, KnowledgeType, TutorContext, TutorScope


def _context(**overrides) -> TutorContext:
    fields = {
        "project_id": 1,
        "curricular_placement": ["guided_practice"],
        "prior_knowledge": "Expanding brackets",
        "known_difficulties": "Sign errors with a negative constant",
        "knowledge_type": KnowledgeType.RULE,
        "learning_goal": "Factor a quadratic using the ac method",
        "tutor_roles": ["practice"],
        "feedback_mode": FeedbackMode.CORRECTIVE,
        "scope": TutorScope.PARTIAL,
    }
    return TutorContext(**(fields | overrides))


@pytest.mark.parametrize("knowledge_type", list(KnowledgeType))
def test_every_knowledge_type_produces_a_different_tutor(knowledge_type):
    """guiding principle: if two answers gave the same parameters,
    the question would not be worth asking."""
    request, _ = derive_request(_context(knowledge_type=knowledge_type))
    pattern = KNOWLEDGE_PATTERNS[knowledge_type]

    assert request.problem_type is pattern.problem_type
    assert request.num_steps == pattern.num_steps
    assert request.use_scaffolds is pattern.use_scaffolds


def test_the_three_patterns_are_actually_distinct():
    shapes = {
        (p.problem_type, p.num_steps, p.num_hints, p.use_scaffolds)
        for p in KNOWLEDGE_PATTERNS.values()
    }
    assert len(shapes) == len(KNOWLEDGE_PATTERNS)


def test_every_derived_value_carries_a_reason():
    """The reason is what the teacher sees next to the pre-filled control."""
    _, derivations = derive_request(_context())

    assert {d.field for d in derivations} == {
        "problem_type",
        "num_steps",
        "num_hints",
        "use_scaffolds",
    }
    assert all(d.reason.strip() for d in derivations)


def test_implicit_feedback_turns_scaffolds_off():
    """OATutor appends a bottom-out Answer entry to every scaffold, so a scaffolded
    pathway reveals the answer whatever the prompt says."""
    request, derivations = derive_request(
        _context(knowledge_type=KnowledgeType.RULE, feedback_mode=FeedbackMode.IMPLICIT)
    )

    # Rule-based would otherwise scaffold.
    assert KNOWLEDGE_PATTERNS[KnowledgeType.RULE].use_scaffolds is True
    assert request.use_scaffolds is False
    reason = next(d.reason for d in derivations if d.field == "use_scaffolds")
    assert "reveals" in reason


@pytest.mark.parametrize(
    ("scope", "expected"),
    [(TutorScope.ADDITION, 2), (TutorScope.PARTIAL, 5), (TutorScope.FULL, 10)],
)
def test_scope_sets_the_task_count(scope, expected):
    slots, derivation = derive_slots(_context(scope=scope))
    assert slots == expected
    assert scope.value in derivation.reason


def test_summary_leaves_out_what_the_teacher_skipped():
    """The optional sections are skippable, so an untouched one must not appear
    as an empty heading."""
    headings = [s.heading for s in build_summary(_context())]

    assert "Learning goal" in headings
    assert "How it has been taught" not in headings
    assert "Constraints" not in headings


def test_summary_reports_what_was_entered():
    context = _context(
        instructional_history="Taught with area models",
        duration_minutes=20,
        location="in class",
    )
    text = summary_text(context)

    assert "Factor a quadratic using the ac method (rule-based knowledge)" in text
    assert "How it has been taught: Taught with area models" in text
    assert "20 minutes; worked on in class" in text
    # Labels, not the stored enum values.
    assert "guided practice" in text
    assert "guided_practice" not in text


def test_the_context_reaches_the_prompt():
    request, _ = derive_request(
        _context(
            prior_knowledge="Expanding brackets",
            known_difficulties="Sign errors with a negative constant",
            terminology="we say the ac method",
        )
    )

    prompt = (
        PROBLEM_PROMPT.invoke(
            {
                "teaching_context": format_teaching_context(request.teaching_context),
                "topic": request.topic,
                "difficulty": "medium",
                "context": "",
                "avoid": "",
            }
        )
        .to_messages()[1]
        .content
    )

    assert "Expanding brackets" in prompt
    assert "Sign errors with a negative constant" in prompt
    assert "we say the ac method" in prompt


def test_a_condition_without_a_context_step_sends_nothing_extra():
    """The control condition has no context, and the prompt must not gain an empty
    heading announcing that."""
    assert format_teaching_context("") == ""
    assert format_teaching_context("   ") == ""


def test_teacher_intents_are_written_out_not_slugged():
    """These reach both the teacher's summary and the model."""
    request, _ = derive_request(_context(teacher_intents=["no_long_text", "class_terminology"]))

    assert "no long explanatory texts" in request.teaching_context
    assert "no_long_text" not in request.teaching_context
