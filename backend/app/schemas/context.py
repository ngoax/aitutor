
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import FeedbackMode, KnowledgeType, TutorScope


class ContextInput(BaseModel):
    """What derivation and the summary read."""

    model_config = ConfigDict(from_attributes=True)

    # Core: each of these changes the tutor.
    curricular_placement: list[str] = Field(default_factory=list)
    prior_knowledge: str = ""
    known_difficulties: str = ""
    knowledge_type: KnowledgeType = KnowledgeType.RULE
    learning_goal: str = ""
    tutor_roles: list[str] = Field(default_factory=list)
    feedback_mode: FeedbackMode = FeedbackMode.CORRECTIVE
    scope: TutorScope = TutorScope.PARTIAL

    # Optional deepening
    instructional_history: str = ""
    representations: str = ""
    terminology: str = ""
    heterogeneity: str = ""
    teacher_intents: list[str] = Field(default_factory=list)
    teacher_intent_note: str = ""
    duration_minutes: int | None = None
    location: str = ""
    group_work: str = ""


class TutorContextUpdate(BaseModel):
    """Teacher edits, saved field by field as they answer."""

    curricular_placement: list[str] | None = None
    prior_knowledge: str | None = None
    known_difficulties: str | None = None
    knowledge_type: KnowledgeType | None = None
    learning_goal: str | None = None
    tutor_roles: list[str] | None = None
    feedback_mode: FeedbackMode | None = None
    scope: TutorScope | None = None
    instructional_history: str | None = None
    representations: str | None = None
    terminology: str | None = None
    heterogeneity: str | None = None
    teacher_intents: list[str] | None = None
    teacher_intent_note: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=240)
    location: str | None = None
    group_work: str | None = None


class TutorContextRead(ContextInput):
    id: int
    project_id: int
    goal_critique: dict[str, Any] = Field(default_factory=dict)
    confirmed_at: datetime | None = None


class SummarySection(BaseModel):
    heading: str
    body: str


class Derivation(BaseModel):
    """One parameter the context decided and why."""

    field: str
    value: Any
    reason: str


class ContextSummaryRead(BaseModel):
    """The summary and what it implies for generation"""

    sections: list[SummarySection]
    derivations: list[Derivation]
    num_slots: int
    complete: bool
    missing: list[str]
