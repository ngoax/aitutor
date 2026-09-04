"""The two grid types grade by opposite routes, which nothing in the corpus shows."""

import json

import pytest
from pydantic import ValidationError

from app.export.exporter import _step_json, export_project
from app.export.oatutor_schema import StepJson
from app.models import AnswerType, ProblemType
from tests.test_export_merge import _answerable


def _as_grid(session, step, problem_type, answer_type):
    _answerable(session, step)
    step.problem_type = problem_type
    step.answer_type = answer_type
    step.step_answer = [["1", "2"], ["3", "4"]]
    step.num_rows = 2
    step.num_cols = 2
    session.commit()
    return step


def test_matrix_exports_as_latex_not_json(session, step):
    _as_grid(session, step, ProblemType.MATRIX_INPUT, AnswerType.ARITHMETIC)

    exported = _step_json(step)

    assert exported.step_answer == ["$$\\begin{bmatrix} 1 & 2 \\\\ 3 & 4 \\end{bmatrix}$$"]
    # parseMatrixTex slices from the space after "matrix} ", so it has to be there.
    assert "{bmatrix} 1" in exported.step_answer[0]
    # The student sizes the widget, so these would be rejected by the schema.
    assert exported.num_rows is None and exported.num_cols is None


def test_grid_exports_as_the_json_the_widget_submits(session, step):
    _as_grid(session, step, ProblemType.GRID_INPUT, AnswerType.STRING)

    exported = _step_json(step)

    assert json.loads(exported.step_answer[0]) == [["1", "2"], ["3", "4"]]
    assert exported.num_rows == 2 and exported.num_cols == 2


@pytest.mark.parametrize(
    ("problem_type", "answer_type", "answer", "match"),
    [
        (ProblemType.MATRIX_INPUT, AnswerType.ARITHMETIC, ['[["1"]]'], "begin"),
        (
            ProblemType.MATRIX_INPUT,
            AnswerType.STRING,
            ["$$\\begin{bmatrix} 1 \\end{bmatrix}$$"],
            "arithmetic",
        ),
        (ProblemType.GRID_INPUT, AnswerType.ARITHMETIC, ['[["1"]]'], "string"),
    ],
)
def test_the_export_contract_rejects_the_wrong_pairing(problem_type, answer_type, answer, match):
    fields = {
        "id": "s1",
        "step_answer": answer,
        "problem_type": problem_type,
        "answer_type": answer_type,
        "step_title": "A step",
    }
    if problem_type is ProblemType.GRID_INPUT:
        fields |= {"num_rows": 1, "num_cols": 1}
    with pytest.raises(ValidationError, match=match):
        StepJson(**fields)


def test_a_matrix_problem_exports_end_to_end(session, step, populated_root):
    _as_grid(session, step, ProblemType.MATRIX_INPUT, AnswerType.ARITHMETIC)
    assert export_project(session, step.problem.project).written == [step.problem.oatutor_id]
