import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.context.derivation import derive_request
from app.core.db import get_session
from app.main import app
from app.models import FeedbackMode, KnowledgeType, Project
from app.schemas.context import ContextInput


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Project(name="Algebra", source_name="algebra"))
        session.commit()
        app.dependency_overrides[get_session] = lambda: session
        yield TestClient(app)
        app.dependency_overrides.clear()


def test_context_is_created_on_first_read(client):
    """The form needs a row to save into, so touching it makes one."""
    response = client.get("/api/projects/1/context")

    assert response.status_code == 200
    assert response.json()["knowledge_type"] == "rule"
    assert response.json()["confirmed_at"] is None


def test_editing_after_confirming_lapses_the_confirmation(client):
    """Otherwise the teacher has agreed to a summary that is no longer on screen."""
    client.patch(
        "/api/projects/1/context",
        json={
            "learning_goal": "Factor a quadratic using the ac method",
            "prior_knowledge": "Expanding brackets",
            "curricular_placement": ["guided_practice"],
            "tutor_roles": ["practice"],
        },
    )
    assert client.post("/api/projects/1/context/confirm").json()["confirmed_at"] is not None

    after = client.patch("/api/projects/1/context", json={"learning_goal": "Something else"})

    assert after.json()["confirmed_at"] is None


def test_confirm_names_what_is_still_missing(client):
    response = client.post("/api/projects/1/context/confirm")

    assert response.status_code == 400
    assert "a learning goal" in response.json()["detail"]


def test_summary_reports_completeness_and_what_it_implies(client):
    client.patch(
        "/api/projects/1/context",
        json={
            "learning_goal": "Factor a quadratic using the ac method",
            "prior_knowledge": "Expanding brackets",
            "curricular_placement": ["guided_practice"],
            "tutor_roles": ["practice"],
            "knowledge_type": "principle",
            "scope": "full",
        },
    )

    body = client.get("/api/projects/1/context/summary").json()

    assert body["complete"] is True
    assert body["missing"] == []
    assert body["num_slots"] == 10
    fields = {d["field"] for d in body["derivations"]}
    assert fields == {"problem_type", "num_steps", "num_hints", "use_scaffolds", "num_slots"}
    assert all(d["reason"] for d in body["derivations"])


def test_derivation_survives_a_json_round_trip():
    context = ContextInput(
        learning_goal="Factor a quadratic",
        knowledge_type=KnowledgeType.RULE,
        feedback_mode=FeedbackMode.IMPLICIT,
    )
    snapshot = context.model_dump(mode="json")
    assert snapshot["feedback_mode"] == "implicit"
    assert snapshot["feedback_mode"] is not FeedbackMode.IMPLICIT

    rehydrated = ContextInput.model_validate(snapshot)

    assert rehydrated.feedback_mode is FeedbackMode.IMPLICIT
    assert derive_request(rehydrated)[0].use_scaffolds is False
