from collections.abc import Callable

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


def call_count(request: GenerationRequest) -> int:
    per_step = 2 if request.num_hints else 1
    return 1 + request.num_steps * per_step


def generate_draft(
    request: GenerationRequest,
    project_id: int,
    config: ProviderConfig | None = None,
    avoid: list[str] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> GeneratedDraft:
    docs = retrieve(
        project_id=project_id,
        query=request.topic,
        k=request.k,
        source_document_id=request.source_document_id,
    )
    total = call_count(request)
    done = 0

    def report() -> None:
        if on_progress is not None:
            on_progress(done, total)

    problem = generate_problem(
        topic=request.topic,
        difficulty=request.difficulty,
        docs=docs,
        config=config,
        avoid=avoid,
        teaching_context=request.teaching_context,
    )
    done += 1
    report()

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
            teaching_context=request.teaching_context,
        )
        done += 1
        report()

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
                teaching_context=request.teaching_context,
            )
            done += 1
            report()
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
        teaching_context=request.teaching_context,
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
            teaching_context=request.teaching_context,
        )
    return DraftStep(step=step, hints=hints)


def generate_alternatives(
    request: GenerationRequest,
    project_id: int,
    count: int,
    config: ProviderConfig | None = None,
) -> list[GeneratedDraft]:

    drafts: list[GeneratedDraft] = []
    for _ in range(count):
        drafts.append(
            generate_draft(
                request,
                project_id=project_id,
                config=config,
                avoid=[draft.problem.body for draft in drafts],
            )
        )
    return drafts
