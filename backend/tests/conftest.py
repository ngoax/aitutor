import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models import Problem, Project, Step


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def step(session):
    project = Project(name="Algebra", source_name="algebra")
    session.add(project)
    session.flush()
    problem = Problem(project_id=project.id, oatutor_id="factoring", title="Factor it")
    session.add(problem)
    session.flush()
    step = Step(problem_id=problem.id, oatutor_id="factoringa", step_title="Product of a and c")
    session.add(step)
    session.commit()
    session.refresh(step)
    return step
