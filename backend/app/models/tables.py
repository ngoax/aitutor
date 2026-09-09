from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import (
    AnswerType,
    AnswerValidator,
    DraftStatus,
    FeedbackMode,
    HintType,
    IngestionStatus,
    KnowledgeType,
    ProblemType,
    RunStatus,
    StudyCondition,
    TutorScope,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _json_column(default_factory) -> Any:
    return Field(default_factory=default_factory, sa_column=Column(JSON))


class Project(SQLModel, table=True):
    __table_args__ = {"sqlite_autoincrement": True}

    id: int | None = Field(default=None, primary_key=True)
    name: str
    # Becomes the OATutor `content-sources/<source_name>` directory on export.
    source_name: str
    license: str = ""
    chat_provider: str | None = None
    chat_model: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    # Which phases of the study this participant runs.
    study_condition: StudyCondition = StudyCondition.CONTEXT_REVIEW
    created_at: datetime = Field(default_factory=_now)

    tutor_context: "TutorContext" = Relationship(
        back_populates="project",
        cascade_delete=True,
        sa_relationship_kwargs={"uselist": False},
    )
    runs: list["GenerationRun"] = Relationship(back_populates="project", cascade_delete=True)
    documents: list["SourceDocument"] = Relationship(back_populates="project", cascade_delete=True)
    problems: list["Problem"] = Relationship(back_populates="project", cascade_delete=True)
    lesson_plans: list["LessonPlan"] = Relationship(back_populates="project", cascade_delete=True)
    skill_defaults: list["SkillDefault"] = Relationship(
        back_populates="project", cascade_delete=True
    )


class SourceDocument(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", ondelete="CASCADE")
    filename: str
    stored_path: str
    content_type: str | None = None
    status: IngestionStatus = IngestionStatus.PENDING
    chunk_count: int = 0
    error: str | None = None
    created_at: datetime = Field(default_factory=_now)

    project: Project = Relationship(back_populates="documents")


class LessonPlan(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", ondelete="CASCADE")
    oatutor_id: str
    name: str
    topics: str = ""
    allow_recycle: bool = True
    # {skill_name: target_mastery}
    learning_objectives: dict[str, float] = _json_column(dict)

    project: Project = Relationship(back_populates="lesson_plans")
    problems: list["Problem"] = Relationship(back_populates="lesson_plan")


class TutorContext(SQLModel, table=True):
    """What the teacher decides before anything is generated"""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", ondelete="CASCADE", unique=True)

    # Core decisions
    curricular_placement: list[str] = _json_column(list)
    prior_knowledge: str = ""
    known_difficulties: str = ""
    knowledge_type: KnowledgeType = KnowledgeType.RULE
    learning_goal: str = ""
    tutor_roles: list[str] = _json_column(list)
    feedback_mode: FeedbackMode = FeedbackMode.CORRECTIVE
    scope: TutorScope = TutorScope.PARTIAL

    # Optional deepening (skippable)
    instructional_history: str = ""
    representations: str = ""
    terminology: str = ""
    heterogeneity: str = ""
    teacher_intents: list[str] = _json_column(list)
    teacher_intent_note: str = ""
    duration_minutes: int | None = None
    location: str = ""
    group_work: str = ""

    # Model's response to the learning goal
    goal_critique: dict[str, Any] = _json_column(dict)
    # Set when the teacher accepts the assembled summary.
    confirmed_at: datetime | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    project: Project = Relationship(back_populates="tutor_context")


class GenerationRun(SQLModel, table=True):
    """One generation producing several alternatives per task slot"""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", ondelete="CASCADE")
    context_snapshot: dict[str, Any] = _json_column(dict)
    request_snapshot: dict[str, Any] = _json_column(dict)
    num_slots: int = 1
    num_alternatives: int = 3
    status: RunStatus = RunStatus.GENERATING
    error: str | None = None
    created_at: datetime = Field(default_factory=_now)

    project: Project = Relationship(back_populates="runs")
    problems: list["Problem"] = Relationship(back_populates="run")


class Problem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", ondelete="CASCADE")
    lesson_plan_id: int | None = Field(default=None, foreign_key="lessonplan.id")
    oatutor_id: str
    title: str
    body: str = ""
    course_name: str = ""
    oer: str | None = None
    variabilization: dict[str, Any] = _json_column(dict)
    topic: str | None = None
    difficulty: str | None = None
    status: DraftStatus = DraftStatus.DRAFT
    # Why generation failed, shown to the teacher. Cleared on a successful run.
    error: str | None = None
    # The wizard inputs that produced this draft, so one step can be regenerated.
    generation_request: dict[str, Any] = _json_column(dict)
    # Chunk ids that grounded this generation for display of sources
    source_chunk_ids: list[str] = _json_column(list)
    progress_done: int = 0
    progress_total: int = 0
    run_id: int | None = Field(default=None, foreign_key="generationrun.id", ondelete="SET NULL")
    # Which candidate this is within its slot; alternatives share a slot.
    slot_index: int = 0
    alternative_index: int = 0
    selected: bool = False
    created_at: datetime = Field(default_factory=_now)

    run: GenerationRun | None = Relationship(back_populates="problems")
    project: Project = Relationship(back_populates="problems")
    lesson_plan: LessonPlan | None = Relationship(back_populates="problems")
    steps: list["Step"] = Relationship(back_populates="problem", cascade_delete=True)


class Step(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    problem_id: int = Field(foreign_key="problem.id", ondelete="CASCADE")
    # The OATutor step id, e.g. "circle1a".
    oatutor_id: str
    order_index: int = 0
    problem_type: ProblemType = ProblemType.TEXT_BOX
    answer_type: AnswerType = AnswerType.STRING
    step_title: str = ""
    step_body: str = ""
    step_answer: Any = _json_column(list)
    answer_validator: AnswerValidator = AnswerValidator.DEFAULT
    choices: list[str] | None = Field(default=None, sa_column=Column(JSON))
    num_rows: int | None = None
    num_cols: int | None = None
    skills: list[str] = _json_column(list)
    variabilization: dict[str, Any] = _json_column(dict)
    stale: bool = False

    problem: Problem = Relationship(back_populates="steps")
    hints: list["HintEntry"] = Relationship(back_populates="step", cascade_delete=True)


class HintEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    step_id: int = Field(foreign_key="step.id", ondelete="CASCADE")
    pathway_name: str = "Default"
    order_index: int = 0
    oatutor_id: str
    type: HintType = HintType.HINT
    title: str = ""
    text: str = ""
    # Indices of earlier entries in this pathway that must be seen first.
    dependencies: list[int] = _json_column(list)
    # Scaffold-only: a scaffold is a mini-problem with its own input widget.
    problem_type: ProblemType | None = None
    answer_type: AnswerType | None = None
    hint_answer: Any | None = Field(default=None, sa_column=Column(JSON))
    choices: list[str] | None = Field(default=None, sa_column=Column(JSON))

    step: Step = Relationship(back_populates="hints")


class SkillDefault(SQLModel, table=True):
    """BKT parameters per skill."""

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", ondelete="CASCADE")
    skill: str
    prob_mastery: float = 0.1
    prob_transit: float = 0.1
    prob_slip: float = 0.1
    prob_guess: float = 0.1

    project: Project = Relationship(back_populates="skill_defaults")
