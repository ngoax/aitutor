from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.generation.output_schemas import GeneratedStep


def format_context(docs: list[Document]) -> str:
    """Gives document chunks a structured format (page number + content) as input for the LLM"""
    context: list[str] = []
    for doc in docs:
        page = doc.metadata.get("page")
        if page is None:
            page = "Missing page"
        else:
            page += 1
        chunk = f"[p.{page}]\n{doc.page_content}"
        context.append(chunk)
    return "\n\n".join(context)


def format_steps(steps: list[GeneratedStep]) -> str:
    """Gives the LLM formatted context about the previous steps"""
    if not steps:
        return "No steps written yet."
    context: list[str] = []
    for n, step in enumerate(steps, start=1):
        chunk = f"[Step {n}: {step.step_title}]\n{step.step_body}"
        context.append(chunk)
    return "\n\n".join(context)


SYSTEM = (
    "You write practice problems for OATutor, an adaptive tutoring system used in "
    "school and university courses.\n\n"
    "Ground everything in the course material provided with each request: use its "
    "notation, terminology and conventions. Do not introduce facts, formulas or values "
    "the material does not support. If it does not cover something the problem would "
    "need, choose a different angle rather than inventing it.\n\n"
    "The course material was extracted from PDF and has lost superscript formatting. "
    "A digit directly after a variable is an exponent: read ax2+bx+c as ax² + bx + c, "
    "and 3x2y as 3x²y. Never reproduce the flattened form in what you write.\n\n"
    "Write for a student meeting this material for the first time, not for an expert. "
    "Write mathematics as LaTeX. Your answer is JSON, so every backslash must be doubled: "
    r"write \\frac, \\sqrt, \\times, \\theta. A single backslash corrupts the output. "
    "Match the language of the course material.\n\n"
    "Difficulty describes how much work the problem takes, not how obscure it is."
)

PROBLEM_HUMAN = (
    "Course material:\n"
    "{context}\n\n"
    "---\n\n"
    "Topic: {topic}\n"
    "Difficulty: {difficulty}\n\n"
    "Write one problem on this topic, grounded in the course material above."
)

PROBLEM_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM),
        ("human", PROBLEM_HUMAN),
    ]
)


STEP_HUMAN = (
    "Course material:\n"
    "{context}\n\n"
    "---\n\n"
    "Problem: {problem_title}\n"
    "{problem_body}\n\n"
    "Steps already written:\n"
    "{previous_steps}\n\n"
    "---\n\n"
    "Write step {step_number} of {num_steps} for this problem. It must move the student "
    "closer to the solution and must not repeat what an earlier step already established."
)

STEP_PROMPT = ChatPromptTemplate.from_messages([("system", SYSTEM), ("human", STEP_HUMAN)])


RETRY_HUMAN = (
    "Your previous answer was rejected because it did not satisfy the required structure:\n"
    "{errors}\n\n"
    "Return a corrected version of the whole answer. Fix only what is listed above and keep "
    "everything else unchanged. Do not explain the correction."
)
