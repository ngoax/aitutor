import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.db import get_session
from app.generation.output_schemas import GeneratedProblem, GeneratedTextBoxStep
from app.generation.pipeline import DraftStep, GeneratedDraft
from app.main import app
from app.models import FeedbackMode, Project
from app.schemas.context import ContextInput

CONTEXT = {
    "learning_goal": "Factor a quadratic using the ac method",
    "prior_knowledge": "Expanding brackets",
    "curricular_placement": ["guided_practice"],
    "tutor_roles": ["practice"],
    "knowledge_type": "rule",
    "feedback_mode": "implicit",
    "scope": "addition",
}


def fake_alternatives(request, project_id, count, config=None):
    return [
        GeneratedDraft(
            problem=GeneratedProblem(title=f"Candidate {n}", body=f"Factor $${n}x^2+3x+2$$."),
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
        for n in range(count)
    ]


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr("app.api.routes.runs.engine", engine)
    monkeypatch.setattr("app.api.routes.runs.generate_alternatives", fake_alternatives)
    with Session(engine) as session:
        session.add(Project(name="Algebra", source_name="algebra"))
        session.commit()
        app.dependency_overrides[get_session] = lambda: session
        yield TestClient(app)
        app.dependency_overrides.clear()


def test_a_run_needs_a_confirmed_context(client):
    client.patch("/api/projects/1/context", json=CONTEXT)

    response = client.post("/api/projects/1/runs", json={"num_alternatives": 3})

    assert response.status_code == 409
    assert "Confirm" in response.json()["detail"]


def test_the_run_snapshots_the_context_that_produced_it(client):
    client.patch("/api/projects/1/context", json=CONTEXT)
    client.post("/api/projects/1/context/confirm")

    run = client.post("/api/projects/1/runs", json={"num_alternatives": 3}).json()

    assert run["num_slots"] == 2
    assert run["num_alternatives"] == 3
    snapshot = ContextInput.model_validate(run["context_snapshot"])
    assert snapshot.feedback_mode is FeedbackMode.IMPLICIT
    assert run["request_snapshot"]["use_scaffolds"] is False


def test_a_later_context_edit_does_not_rewrite_the_snapshot(client):
    client.patch("/api/projects/1/context", json=CONTEXT)
    client.post("/api/projects/1/context/confirm")
    run_id = client.post("/api/projects/1/runs", json={"num_alternatives": 3}).json()["id"]

    client.patch("/api/projects/1/context", json={"learning_goal": "Something else entirely"})

    stored = client.get(f"/api/projects/1/runs/{run_id}").json()
    assert stored["context_snapshot"]["learning_goal"] == CONTEXT["learning_goal"]


def test_a_failed_run_records_why(client, monkeypatch):

    def boom(**kwargs):
        raise RuntimeError("the provider fell over")

    monkeypatch.setattr("app.api.routes.runs.generate_alternatives", boom)
    client.patch("/api/projects/1/context", json=CONTEXT)
    client.post("/api/projects/1/context/confirm")
    run_id = client.post("/api/projects/1/runs", json={"num_alternatives": 3}).json()["id"]

    stored = client.get(f"/api/projects/1/runs/{run_id}").json()

    assert stored["status"] == "failed"
    assert "the provider fell over" in stored["error"]


def test_a_run_stores_every_alternative_against_its_slot(client):
    client.patch("/api/projects/1/context", json=CONTEXT)
    client.post("/api/projects/1/context/confirm")
    run_id = client.post("/api/projects/1/runs", json={"num_alternatives": 3}).json()["id"]

    stored = client.get(f"/api/projects/1/runs/{run_id}").json()

    assert stored["status"] == "ready"
    assert [slot["slot_index"] for slot in stored["slots"]] == [0, 1]
    for slot in stored["slots"]:
        assert len(slot["alternatives"]) == 3
        # Distinct rows, not the same problem listed three times.
        assert len({p["id"] for p in slot["alternatives"]}) == 3
        assert len({p["oatutor_id"] for p in slot["alternatives"]}) == 3
