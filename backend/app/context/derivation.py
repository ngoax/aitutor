"""Turn a teacher's context into generation parameters, with a reason for each."""

from pydantic import BaseModel

from app.models import FeedbackMode, KnowledgeType, ProblemType, TutorScope
from app.schemas.context import ContextInput, Derivation
from app.schemas.generation import GenerationRequest


class KnowledgePattern(BaseModel):
    """What a knowledge type implies about task shape"""

    problem_type: ProblemType
    num_steps: int
    num_hints: int
    use_scaffolds: bool
    reason: str


KNOWLEDGE_PATTERNS: dict[KnowledgeType, KnowledgePattern] = {
    KnowledgeType.FACT: KnowledgePattern(
        problem_type=ProblemType.TEXT_BOX,
        num_steps=1,
        num_hints=2,
        use_scaffolds=False,
        reason=(
            "Fact knowledge is built by retrieval, so the tutor asks many short "
            "single-step questions rather than working through a method."
        ),
    ),
    KnowledgeType.RULE: KnowledgePattern(
        problem_type=ProblemType.TEXT_BOX,
        num_steps=3,
        num_hints=3,
        use_scaffolds=True,
        reason=(
            "Rule-based knowledge is built by working through examples, so the tutor "
            "breaks each task into steps and asks for the intermediate values."
        ),
    ),
    KnowledgeType.PRINCIPLE: KnowledgePattern(
        problem_type=ProblemType.MULTIPLE_CHOICE,
        num_steps=2,
        num_hints=3,
        use_scaffolds=True,
        reason=(
            "Principle-based knowledge is built by comparing cases, so the tutor sets "
            "fewer, deeper tasks that ask the student to choose and justify."
        ),
    ),
}

# How much of a learning unit the tutor covers, as a number of task slots.
SCOPE_SLOTS: dict[TutorScope, int] = {
    TutorScope.ADDITION: 2,
    TutorScope.PARTIAL: 5,
    TutorScope.FULL: 10,
}


def derive_request(context: ContextInput) -> tuple[GenerationRequest, list[Derivation]]:
    """The parameters this context implies, each with the reason shown to the teacher"""
    pattern = KNOWLEDGE_PATTERNS[context.knowledge_type]
    derivations = [
        Derivation(field="problem_type", value=pattern.problem_type, reason=pattern.reason),
        Derivation(field="num_steps", value=pattern.num_steps, reason=pattern.reason),
        Derivation(field="num_hints", value=pattern.num_hints, reason=pattern.reason),
    ]

    use_scaffolds = pattern.use_scaffolds
    if context.feedback_mode is FeedbackMode.IMPLICIT:
        # OATutor appends a bottom-out "Answer" entry to every scaffold, so a
        # scaffolded pathway hands over the answer whatever the prompt says
        use_scaffolds = False
        derivations.append(
            Derivation(
                field="use_scaffolds",
                value=False,
                reason=(
                    "You asked for hints that stop short of the answer. OATutor reveals "
                    "the answer to every scaffold automatically, so scaffolds are off."
                ),
            )
        )
    else:
        derivations.append(
            Derivation(field="use_scaffolds", value=use_scaffolds, reason=pattern.reason)
        )

    request = GenerationRequest(
        topic=context.learning_goal or "the learning goal",
        problem_type=pattern.problem_type,
        num_steps=pattern.num_steps,
        num_hints=pattern.num_hints,
        use_scaffolds=use_scaffolds,
    )
    return request, derivations


def derive_slots(context: ContextInput) -> tuple[int, Derivation]:
    """How many task slots the tutor should have."""
    slots = SCOPE_SLOTS[context.scope]
    return slots, Derivation(
        field="num_slots",
        value=slots,
        reason=f"You described the tutor as {context.scope.value}, which is {slots} tasks.",
    )
