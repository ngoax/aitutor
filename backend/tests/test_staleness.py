"""Regenerating one step leaves the ones after it written against the old version."""

from app.generation.output_schemas import GeneratedHintPathway, GeneratedTextBoxStep
from app.generation.persist import replace_step
from app.generation.pipeline import DraftStep
from app.models import AnswerType, Problem, ProblemType, Step


def _steps(session, problem, count=4):
    made = []
    for index in range(count):
        step = Step(
            problem_id=problem.id,
            oatutor_id=f"{problem.oatutor_id}{chr(ord('a') + index)}",
            order_index=index,
            problem_type=ProblemType.TEXT_BOX,
            answer_type=AnswerType.ARITHMETIC,
            step_title=f"Step {index}",
            step_body="A question",
            step_answer=["$$1$$"],
        )
        session.add(step)
        made.append(step)
    session.commit()
    return made


def _replacement():
    return DraftStep(
        step=GeneratedTextBoxStep(
            step_title="Rewritten",
            step_body="A different question",
            step_answer=["$$2$$"],
            answer_type="arithmetic",
        ),
        hints=GeneratedHintPathway.model_validate(
            {"hints": [{"title": "The answer", "text": "It is $$2$$."}]}
        ),
    )


def _fresh(session, steps):
    return [session.get(Step, s.id).stale for s in steps]


def test_regenerating_marks_only_what_follows(session, step):
    made = _steps(session, step.problem)

    replace_step(session, made[1], _replacement(), ProblemType.TEXT_BOX)

    # The rewritten step is current; the ones before it never saw the change.
    assert _fresh(session, made) == [False, False, True, True]


def test_regenerating_the_last_step_marks_nothing(session, step):
    made = _steps(session, step.problem)

    replace_step(session, made[-1], _replacement(), ProblemType.TEXT_BOX)

    assert _fresh(session, made) == [False, False, False, False]


def test_regenerating_a_stale_step_clears_its_own_flag(session, step):
    made = _steps(session, step.problem)
    replace_step(session, made[0], _replacement(), ProblemType.TEXT_BOX)
    assert _fresh(session, made) == [False, True, True, True]

    replace_step(session, made[2], _replacement(), ProblemType.TEXT_BOX)

    # 2 is rewritten against current siblings; 1 is still stale, 3 stale again.
    assert _fresh(session, made) == [False, True, False, True]


def test_staleness_does_not_leak_between_problems(session, step):
    """The query filters on problem_id, and a sibling problem shares order_index."""
    neighbour = Problem(
        project_id=step.problem.project_id, oatutor_id="other", title="Another problem"
    )
    session.add(neighbour)
    session.commit()
    theirs = _steps(session, neighbour, count=2)
    made = _steps(session, step.problem)

    replace_step(session, made[0], _replacement(), ProblemType.TEXT_BOX)

    assert _fresh(session, made) == [False, True, True, True]
    assert _fresh(session, theirs) == [False, False]
