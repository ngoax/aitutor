"""Assemble the Context Summary the teacher confirms before anything is generated."""

from app.schemas.context import ContextInput, SummarySection

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

INTENT_LABELS: dict[str, str] = {
    "no_gamification": "no gamification",
    "no_long_text": "no long explanatory texts",
    "explain_reasoning": "learners should explain their reasoning",
    "class_examples": "examples should connect to current classroom content",
    "class_terminology": "use the terminology introduced in class",
}

KNOWLEDGE_LABELS: dict[str, str] = {
    "fact": "fact knowledge",
    "rule": "rule-based knowledge",
    "principle": "principle-based knowledge",
}

FEEDBACK_LABELS: dict[str, str] = {
    "corrective": "the last hint gives the correct answer",
    "implicit": "the hints stop short of the correct answer",
}


def _join(values: list[str], labels: dict[str, str]) -> str:
    return ", ".join(labels.get(value, value) for value in values)


def build_summary(context: ContextInput) -> list[SummarySection]:
    """The confirmable summary. Sections the teacher left empty are left out
    rather than shown blank, so what appears is what they actually decided."""
    setting = " ".join(part for part in (context.location, context.group_work) if part)
    constraints = [
        part
        for part in (
            f"{context.duration_minutes} minutes" if context.duration_minutes else "",
            f"worked on {setting}" if setting else "",
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
        ("How it has been taught", context.instructional_history),
        ("Representations already used", context.representations),
        ("Terminology used in class", context.terminology),
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
                for part in (
                    _join(context.teacher_intents, INTENT_LABELS),
                    context.teacher_intent_note,
                )
                if part
            ),
        ),
        ("Constraints", "; ".join(constraints)),
    ]
    return [SummarySection(heading=h, body=b) for h, b in candidates if b.strip()]


def summary_text(context: ContextInput) -> str:
    """The same summary as one block, which is what reaches the prompt."""
    return "\n".join(f"{s.heading}: {s.body}" for s in build_summary(context))
