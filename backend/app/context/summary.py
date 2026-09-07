"""Assemble the Context Summary the teacher confirms before anything is generated."""

from pydantic import BaseModel

from app.models import TutorContext

PLACEMENT_LABELS: dict[str, str] = {
    "introduction": "introduction to a new topic",
    "after_instruction": "after teacher-led instruction",
    "guided_practice": "guided practice",
    "independent_practice": "independent practice",
    "consolidation": "consolidation",
    "revision": "revision",
    "struggling": "support for struggling learners",
    "transfer": "transfer",
    "application": "application",
    "homework": "homework",
    "exam_preparation": "exam preparation",
}

ROLE_LABELS: dict[str, str] = {
    "explain": "explain new content",
    "practice": "provide practice",
    "diagnose": "identify misconceptions",
    "feedback": "give feedback on answers",
    "differentiation": "offer extension or transfer",
    "review": "support retrieval and consolidation",
}

KNOWLEDGE_LABELS: dict[str, str] = {
    "fact": "fact knowledge",
    "rule": "rule-based knowledge",
    "principle": "principle-based knowledge",
}

FEEDBACK_LABELS: dict[str, str] = {
    "corrective": "the correct answer is shown",
    "implicit": "hints only, stopping short of the answer",
}


class SummarySection(BaseModel):
    heading: str
    body: str


def _join(values: list[str], labels: dict[str, str]) -> str:
    return ", ".join(labels.get(value, value) for value in values)


def build_summary(context: TutorContext) -> list[SummarySection]:
    """The confirmable summary. Sections the teacher left empty are left out
    rather than shown blank, so what appears is what they actually decided."""
    constraints = [
        part
        for part in (
            f"{context.duration_minutes} minutes" if context.duration_minutes else "",
            context.location,
            context.group_work,
        )
        if part
    ]

    candidates = [
        ("Instructional placement", _join(context.curricular_placement, PLACEMENT_LABELS)),
        ("Prior knowledge", context.prior_knowledge),
        ("Known difficulties", context.known_difficulties),
        ("Learners", context.heterogeneity),
        (
            "Learning goal",
            f"{context.learning_goal} ({KNOWLEDGE_LABELS[context.knowledge_type.value]})".strip()
            if context.learning_goal
            else "",
        ),
        (
            "Instructional continuity",
            "; ".join(
                part
                for part in (
                    context.instructional_history,
                    context.representations,
                    context.terminology,
                )
                if part
            ),
        ),
        (
            "Tutor role",
            "; ".join(
                part
                for part in (
                    _join(context.tutor_roles, ROLE_LABELS),
                    FEEDBACK_LABELS[context.feedback_mode.value],
                )
                if part
            ),
        ),
        (
            "Teacher intent",
            "; ".join(
                part
                for part in (", ".join(context.teacher_intents), context.teacher_intent_note)
                if part
            ),
        ),
        ("Constraints", "; ".join(constraints)),
    ]
    return [SummarySection(heading=h, body=b) for h, b in candidates if b.strip()]


def summary_text(context: TutorContext) -> str:
    """The same summary as one block, which is what reaches the prompt."""
    return "\n".join(f"{s.heading}: {s.body}" for s in build_summary(context))
