from typing import Any, TypeVar

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ValidationError

from app.generation.output_schemas import (
    GeneratedGridStep,
    GeneratedHintPathway,
    GeneratedMultipleChoiceStep,
    GeneratedProblem,
    GeneratedStep,
    GeneratedTextBoxStep,
)
from app.generation.prompts import (
    HINT_PROMPT,
    PROBLEM_PROMPT,
    RETRY_HUMAN,
    STEP_PROMPT,
    format_context,
    format_steps,
)
from app.llm.errors import is_transient
from app.llm.factory import get_chat_model
from app.llm.provider_config import ProviderConfig
from app.models import ProblemType

T = TypeVar("T", bound=BaseModel)


def _generate(
    prompt: ChatPromptTemplate,
    variables: dict[str, Any],
    schema: type[T],
    config: ProviderConfig | None = None,
    attempts: int = 3,
) -> T:
    config = config or ProviderConfig()
    chat_model = get_chat_model(config)
    method = config.resolved_structured_method()
    if method is None:
        model = chat_model.with_structured_output(schema)
    else:
        model = chat_model.with_structured_output(schema, method=method)
    messages = prompt.invoke(variables).to_messages()

    last_error: str | None = None
    for _ in range(attempts):
        try:
            result = model.invoke(messages)
        except ValidationError as exc:
            last_error = "; ".join(
                f"{'.'.join(str(loc) for loc in e['loc']) or schema.__name__}: {e['msg']}"
                for e in exc.errors()
            )
        except Exception as exc:
            if not is_transient(exc):
                raise
            last_error = f"{type(exc).__name__} from the provider"
            continue
        else:
            if isinstance(result, schema):
                return result
            last_error = f"expected {schema.__name__}, got {result!r}"
        messages.append(HumanMessage(content=RETRY_HUMAN.format(errors=last_error)))
    raise ValueError(f"Generation failed after {attempts} attempts: {last_error}")


def generate_problem(
    topic: str, difficulty: str, docs: list[Document], config: ProviderConfig | None = None
) -> GeneratedProblem:
    return _generate(
        PROBLEM_PROMPT,
        {"topic": topic, "difficulty": difficulty, "context": format_context(docs)},
        GeneratedProblem,
        config,
    )


def generate_hints(
    step: GeneratedStep,
    previous_steps: list[GeneratedStep],
    problem: GeneratedProblem,
    num_hints: int,
    docs: list[Document],
    config: ProviderConfig | None = None,
) -> GeneratedHintPathway:
    return _generate(
        HINT_PROMPT,
        {
            "context": format_context(docs),
            "problem_title": problem.title,
            "problem_body": problem.body,
            "step_body": step.step_body,
            "step_answer": step.answer_text(),
            "num_hints": num_hints,
            "previous_steps": format_steps(previous_steps),
        },
        GeneratedHintPathway,
        config,
    )


STEP_SCHEMAS: dict[ProblemType, type[GeneratedStep]] = {
    ProblemType.TEXT_BOX: GeneratedTextBoxStep,
    ProblemType.MULTIPLE_CHOICE: GeneratedMultipleChoiceStep,
    # Grid and Matrix are structurally considered to be the same
    ProblemType.MATRIX_INPUT: GeneratedGridStep,
    ProblemType.GRID_INPUT: GeneratedGridStep,
}


def generate_step(
    problem_title: str,
    problem_body: str,
    previous_steps: list[GeneratedStep],
    step_number: int,
    num_steps: int,
    problem_type: ProblemType,
    docs: list[Document],
    config: ProviderConfig | None = None,
) -> GeneratedStep:
    schema = STEP_SCHEMAS[problem_type]
    return _generate(
        STEP_PROMPT,
        {
            "context": format_context(docs),
            "problem_title": problem_title,
            "problem_body": problem_body,
            "previous_steps": format_steps(previous_steps),
            "step_number": step_number,
            "num_steps": num_steps,
        },
        schema,
        config,
    )
