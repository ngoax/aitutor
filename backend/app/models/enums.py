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
