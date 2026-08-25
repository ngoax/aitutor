from typing import Any, TypeVar

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, ValidationError

from app.generation.output_schemas import (
    GeneratedGridStep,
    GeneratedMultipleChoiceStep,
    GeneratedProblem,
    GeneratedStep,
    GeneratedTextBoxStep,
)
from app.generation.prompts import (
    PROBLEM_PROMPT,
    RETRY_HUMAN,
    STEP_PROMPT,
    format_context,
    format_steps,
)
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
    model = get_chat_model(config).with_structured_output(
        schema, method=config.resolved_structured_method()
    )
    messages = prompt.invoke(variables).to_messages()

    last_error: str | None = None
    for _ in range(attempts):
        try:
            result = model.invoke(messages)
            if isinstance(result, schema):
                return result
            last_error = f"expected {schema.__name__}, got {result!r}"
        except ValidationError as exc:
            last_error = "; ".join(
                f"{'.'.join(str(loc) for loc in e['loc']) or schema.__name__}: {e['msg']}"
                for e in exc.errors()
            )
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
