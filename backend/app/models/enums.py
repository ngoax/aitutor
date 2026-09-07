from enum import StrEnum


class ProblemType(StrEnum):
    """The input types OATutor currently supports"""

    TEXT_BOX = "TextBox"
    MULTIPLE_CHOICE = "MultipleChoice"
    GRID_INPUT = "GridInput"
    MATRIX_INPUT = "MatrixInput"


class AnswerType(StrEnum):
    ARITHMETIC = "arithmetic"
    NUMERIC = "numeric"
    STRING = "string"


class AnswerValidator(StrEnum):
    DEFAULT = "default"
    SIMPLIFIED = "simplified"


class HintType(StrEnum):
    HINT = "hint"
    SCAFFOLD = "scaffold"
    SOLUTION = "solution"


class IngestionStatus(StrEnum):
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"


class DraftStatus(StrEnum):
    GENERATING = "generating"
    FAILED = "failed"
    DRAFT = "draft"
    EDITED = "edited"
    EXPORT_READY = "export_ready"


class StudyCondition(StrEnum):
    """Which phases of the study a participant runs."""

    CONTROL = "control"
    CONTEXT = "context"
    REVIEW = "review"
    CONTEXT_REVIEW = "context_review"

    @property
    def has_context(self) -> bool:
        return self in (StudyCondition.CONTEXT, StudyCondition.CONTEXT_REVIEW)

    @property
    def has_review(self) -> bool:
        return self in (StudyCondition.REVIEW, StudyCondition.CONTEXT_REVIEW)


class KnowledgeType(StrEnum):
    """KLI knowledge components. Decides which instructional pattern fits."""

    FACT = "fact"
    RULE = "rule"
    PRINCIPLE = "principle"


class FeedbackMode(StrEnum):
    CORRECTIVE = "corrective"
    IMPLICIT = "implicit"


class TutorScope(StrEnum):
    """How much of a learning unit the tutor covers, which sets the task count."""

    ADDITION = "addition"
    PARTIAL = "partial"
    FULL = "full"


class RunStatus(StrEnum):
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
