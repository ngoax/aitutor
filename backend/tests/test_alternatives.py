import pytest

from app.generation.output_schemas import GeneratedProblem, GeneratedTextBoxStep
from app.generation.pipeline import DraftStep, GeneratedDraft, generate_alternatives
from app.schemas.generation import GenerationRequest

REQUEST = GenerationRequest(topic="factoring a quadratic", num_steps=1, num_hints=0)


def _draft(n: int) -> GeneratedDraft:
    return GeneratedDraft(
        problem=GeneratedProblem(title=f"Problem {n}", body=f"Factor $${n}x^2+3x+2$$."),
        steps=[
            DraftStep(
                step=GeneratedTextBoxStep(
                    step_title="The product",
                    step_body="What is $$ac$$?",
                    step_answer=[f"$${n * 2}$$"],
                    answer_type="arithmetic",
                )
            )
        ],
    )


@pytest.fixture
def fake_generation(monkeypatch):
    calls: list[dict] = []

    def fake_generate_draft(request, project_id, config=None, **kwargs):
        calls.append({"request": request, "kwargs": kwargs})
        signature = (request.topic, request.difficulty, repr(sorted(kwargs.items())))
        return _draft(abs(hash(signature)) % 1000)

    monkeypatch.setattr("app.generation.pipeline.generate_draft", fake_generate_draft)
    return calls


def test_returns_exactly_the_number_asked_for(fake_generation):
    drafts = generate_alternatives(REQUEST, project_id=1, count=3)

    assert len(drafts) == 3


def test_each_alternative_is_a_complete_draft(fake_generation):
    drafts = generate_alternatives(REQUEST, project_id=1, count=3)

    for draft in drafts:
        assert isinstance(draft, GeneratedDraft)
        assert draft.problem.title
        assert len(draft.steps) == REQUEST.num_steps


def test_alternatives_are_not_all_the_same(fake_generation):
    drafts = generate_alternatives(REQUEST, project_id=1, count=3)

    bodies = {draft.problem.body for draft in drafts}
    assert len(bodies) == 3, (
        "every call was made with the same inputs, so the model repeated itself"
    )
