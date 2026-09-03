from pydantic import BaseModel

from app.generation.chains import generate_hints, generate_problem, generate_step
from app.generation.output_schemas import GeneratedHintPathway, GeneratedProblem, GeneratedStep
from app.llm.provider_config import ProviderConfig
from app.rag.retriever import retrieve
from app.schemas.generation import GenerationRequest


class DraftStep(BaseModel):
    step: GeneratedStep
    hints: GeneratedHintPathway | None = None


class GeneratedDraft(BaseModel):
    problem: GeneratedProblem
    steps: list[DraftStep]


def generate_draft(
    request: GenerationRequest,
    project_id: int,
    config: ProviderConfig | None = None,
) -> GeneratedDraft:
    docs = retrieve(
        project_id=project_id,
        query=request.topic,
        k=request.k,
        source_document_id=request.source_document_id,
    )
    problem = generate_problem(
        topic=request.topic,
        difficulty=request.difficulty,
        docs=docs,
        config=config,
    )

    previous: list[GeneratedStep] = []
    draft_steps: list[DraftStep] = []
    for number in range(1, request.num_steps + 1):
        step = generate_step(
            problem_title=problem.title,
            problem_body=problem.body,
            previous_steps=previous,
            step_number=number,
            num_steps=request.num_steps,
            problem_type=request.problem_type,
            docs=docs,
            config=config,
        )
        hints = None
        if request.num_hints:
            hints = generate_hints(
                step=step,
                previous_steps=previous,
                problem=problem,
                num_hints=request.num_hints,
                docs=docs,
                config=config,
                use_scaffolds=request.use_scaffolds,
            )
        draft_steps.append(DraftStep(step=step, hints=hints))
        previous.append(step)

    return GeneratedDraft(problem=problem, steps=draft_steps)


def regenerate_step(
    request: GenerationRequest,
    project_id: int,
    problem: GeneratedProblem,
    previous_steps: list[GeneratedStep],
    step_number: int,
    config: ProviderConfig | None = None,
) -> DraftStep:
    """Generate replacement step when user is not content with current generated step"""
    docs = retrieve(
        project_id=project_id,
        query=request.topic,
        k=request.k,
        source_document_id=request.source_document_id,
    )
    step = generate_step(
        problem_title=problem.title,
        problem_body=problem.body,
        previous_steps=previous_steps,
        step_number=step_number,
        num_steps=request.num_steps,
        problem_type=request.problem_type,
        docs=docs,
        config=config,
    )

    hints = None
    if request.num_hints != 0:
        hints = generate_hints(
            step=step,
            previous_steps=previous_steps,
            problem=problem,
            num_hints=request.num_hints,
            docs=docs,
            config=config,
            use_scaffolds=request.use_scaffolds,
        )
    return DraftStep(step=step, hints=hints)
