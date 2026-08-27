"""Turn a generated draft into Problem, Step and HintEntry rows.

The generation schemas deliberately omit anything the server owns (ids, ordering,
hint types), so this module fills those in and reshapes each step type's answer
into the form the Step table stores.
"""

import re
import string

from sqlmodel import Session, select

from app.generation.output_schemas import (
    GeneratedGridStep,
    GeneratedMultipleChoiceStep,
    GeneratedStep,
    GeneratedTextBoxStep,
)
from app.generation.pipeline import GeneratedDraft
from app.models import AnswerType, HintEntry, HintType, Problem, ProblemType, Step
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


def persist_draft(
    session: Session,
    project_id: int,
    request: GenerationRequest,
    draft: GeneratedDraft,
) -> Problem:
    problem = Problem(
        project_id=project_id,
        oatutor_id=unique_problem_id(session, project_id, slugify(draft.problem.title)),
        title=draft.problem.title,
        body=draft.problem.body,
        topic=request.topic,
        difficulty=request.difficulty,
    )
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

        hints = draft_step.hints.hints
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

    session.commit()
    session.refresh(problem)
    return problem
