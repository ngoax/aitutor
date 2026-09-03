"""Merging into a populated OATutor, which is what the standalone path never exercises."""

import json

import pytest

from app.core.config import settings
from app.export.exporter import export_project
from app.models import AnswerType, HintEntry, HintType, Step


@pytest.fixture
def populated_root(tmp_path, monkeypatch):
    """An OATutor content source that already holds someone else's course."""
    (tmp_path / "skillModel.json").write_text(json.dumps({"их_step": ["someone_elses_skill"]}))
    monkeypatch.setattr(settings, "oatutor_content_dir", tmp_path)
    return tmp_path


def _answerable(session, step: Step) -> None:
    step.step_answer = ["$$24$$"]
    step.skills = ["our_skill"]
    session.add(step)
    session.add(
        HintEntry(
            step_id=step.id,
            order_index=0,
            oatutor_id=f"{step.oatutor_id}-h1",
            type=HintType.SOLUTION,
            title="The answer",
            text="It is $$24$$.",
        )
    )
    session.commit()


def test_lesson_lists_only_its_own_skills(session, step, populated_root):
    _answerable(session, step)
    project = step.problem.project

    result = export_project(session, project)
    assert result.written == [step.problem.oatutor_id]

    plans = json.loads((populated_root / "coursePlans.json").read_text())
    course = next(c for c in plans if c["courseName"] == project.name)
    assert course["lessons"][0]["learningObjectives"] == {"our_skill": 0.85}

    # The other course's skills survive in the model itself, just not in our lesson.
    skills = json.loads((populated_root / "skillModel.json").read_text())
    assert skills["их_step"] == ["someone_elses_skill"]
    assert skills[step.oatutor_id] == ["our_skill"]


def test_tuned_bkt_parameters_survive_re_export(session, step, populated_root):
    _answerable(session, step)
    project = step.problem.project
    export_project(session, project)

    params = populated_root / "bkt-params" / "defaultBKTParams.json"
    tuned = json.loads(params.read_text())
    tuned["our_skill"]["probMastery"] = 0.42
    params.write_text(json.dumps(tuned))

    export_project(session, project)
    assert json.loads(params.read_text())["our_skill"]["probMastery"] == 0.42


def test_stray_dollar_in_rendered_text(session, step, populated_root):
    _answerable(session, step)
    step.step_title = "Product $ac$"
    session.commit()

    result = export_project(session, step.problem.project)
    assert result.written == []
    assert "single $" in result.skipped[step.problem.oatutor_id]


def test_string_answer_may_keep_dollar(session, step, populated_root):
    _answerable(session, step)
    step.answer_type = AnswerType.STRING
    step.step_answer = ["$5"]
    session.commit()

    result = export_project(session, step.problem.project)
    assert result.written == [step.problem.oatutor_id]


def test_skipped_problem_that_was_exported_before(session, step, populated_root):
    _answerable(session, step)
    project = step.problem.project
    assert export_project(session, project).written == [step.problem.oatutor_id]

    step.step_title = "Product $ac$"
    session.commit()

    result = export_project(session, project)
    assert result.written == []
    assert "still being served" in result.skipped[step.problem.oatutor_id]


def test_arithmetic_answer_with_comma(session, step, populated_root):
    _answerable(session, step)
    step.answer_type = AnswerType.ARITHMETIC
    step.step_answer = ["$$-9,8$$", "$$8,-9$$"]
    session.commit()

    result = export_project(session, step.problem.project)
    assert result.written == []
    assert "comma" in result.skipped[step.problem.oatutor_id]


def test_the_same_answer_passes_as_string(session, step, populated_root):
    """String answers are compared literally, so a list of values works there."""
    _answerable(session, step)
    step.answer_type = AnswerType.STRING
    step.step_answer = ["-9,8", "8,-9"]
    session.commit()

    assert export_project(session, step.problem.project).written == [step.problem.oatutor_id]
