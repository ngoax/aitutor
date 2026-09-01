"""Turn a generated draft into Problem, Step and HintEntry rows, and back again.

The generation schemas omit anything the server owns (ids, ordering, hint types),
so this module fills those in and reshapes each step type's answer for the Step
table. Regenerating one step needs the reverse direction too.
"""

import re
import string
from collections.abc import Iterable

from sqlmodel import Session, select

from app.generation.output_schemas import (
    GeneratedGridStep,
    GeneratedHint,
    GeneratedMultipleChoiceStep,
    GeneratedProblem,
    GeneratedStep,
    GeneratedTextBoxStep,
)
from app.generation.pipeline import DraftStep, GeneratedDraft
from app.models import (
    AnswerType,
    DraftStatus,
    HintEntry,
    HintType,
    Problem,
    ProblemType,
    Step,
)
from app.schemas.generation import GenerationRequest

MAX_SLUG_LENGTH = 40


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:MAX_SLUG_LENGTH]
    return slug or "problem"


def unique_problem_id(session: Session, project_id: int, base: str) -> str:
    """Add suffix until it is free within the project.

    oatutor_id becomes a directory name under content-pool, so collisions would
    make one problem overwrite another on export.
    """
    taken = set(
        session.exec(select(Problem.oatutor_id).where(Problem.project_id == project_id)).all()
    )
    if base not in taken:
        return base
    suffix = 2
    while f"{base}_{suffix}" in taken:
        suffix += 1
    return f"{base}_{suffix}"


def as_generated_problem(problem: Problem) -> GeneratedProblem:
    """The stored problem in the shape the prompts expect"""
    return GeneratedProblem(title=problem.title, body=problem.body)


def as_generated_steps(steps: Iterable[Step]) -> list[GeneratedStep]:
    """Stored steps as prompt context. format_steps only reads title and body,
    which is exactly what the base class carries."""
    return [GeneratedStep(step_title=step.step_title, step_body=step.step_body) for step in steps]


def step_columns(generated: GeneratedStep, problem_type: ProblemType) -> dict:
    """Map one generated step onto the columns Step stores."""
    columns: dict = {
        "problem_type": problem_type,
        "step_title": generated.step_title,
        "step_body": generated.step_body,
    }

    if isinstance(generated, GeneratedTextBoxStep):
        columns["step_answer"] = generated.step_answer
        columns["answer_type"] = generated.answer_type
    elif isinstance(generated, GeneratedMultipleChoiceStep):
        # OATutor compares choices as strings, so MultipleChoice is always answerType string.
        columns["step_answer"] = [generated.step_answer]
        columns["choices"] = generated.choices
        columns["answer_type"] = AnswerType.STRING
    elif isinstance(generated, GeneratedGridStep):
        # Flat rows exist because nested lists are unreliable to generate.
        # This is where they become the list of lists the Step column holds.
        columns["step_answer"] = [row.split("|") for row in generated.rows]
        columns["num_rows"] = generated.num_rows
        columns["num_cols"] = generated.num_cols
    else:
        raise ValueError(f"No column mapping for {type(generated).__name__}")

    return columns


def add_hints(session: Session, step: Step, hints: list[GeneratedHint]) -> None:
    """Write a hint pathway. The last entry states the answer, and each one
    depends on the previous so OATutor reveals them in order."""
    for position, hint in enumerate(hints):
        session.add(
            HintEntry(
                step_id=step.id,
                order_index=position,
                oatutor_id=f"{step.oatutor_id}h{position + 1}",
                type=HintType.SOLUTION if position == len(hints) - 1 else HintType.HINT,
                title=hint.title,
                text=hint.text,
                dependencies=[position - 1] if position else [],
            )
        )


def persist_draft(
    session: Session,
    problem: Problem,
    request: GenerationRequest,
    draft: GeneratedDraft,
) -> Problem:
    """Fill a placeholder Problem row with the generated draft.

    The row already exists because generation runs in the background: it is
    created up front so the client has something to poll.
    """
    problem.title = draft.problem.title
    problem.body = draft.problem.body
    problem.status = DraftStatus.DRAFT
    problem.error = None
    session.add(problem)
    session.flush()

    for index, draft_step in enumerate(draft.steps):
        step = Step(
            problem_id=problem.id,
            oatutor_id=f"{problem.oatutor_id}{string.ascii_lowercase[index]}",
            order_index=index,
            **step_columns(draft_step.step, request.problem_type),
        )
        session.add(step)
        session.flush()

        if draft_step.hints is None:
            continue
        add_hints(session, step, draft_step.hints.hints)

    session.commit()
    session.refresh(problem)
    return problem


# Cleared before each write so a regenerated step cannot inherit them.
TYPE_SPECIFIC_COLUMNS = {"choices": None, "num_rows": None, "num_cols": None}


def replace_step(
    session: Session, step: Step, draft_step: DraftStep, problem_type: ProblemType
) -> Step:
    """Overwrite one step in place. oatutor_id and order_index survive, since
    later steps are numbered from the same sequence."""
    for column, value in (
        TYPE_SPECIFIC_COLUMNS | step_columns(draft_step.step, problem_type)
    ).items():
        setattr(step, column, value)
    session.add(step)

    for hint in list(step.hints):
        session.delete(hint)
    session.flush()

    if draft_step.hints is not None:
        add_hints(session, step, draft_step.hints.hints)

    session.commit()
    session.refresh(step)
    return step
