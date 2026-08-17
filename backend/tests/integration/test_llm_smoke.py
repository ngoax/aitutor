"""Live smoke tests for multi provider use (app.llm.factory).
uv run pytest -m integration
"""

import pytest
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.llm.factory import get_chat_model
from app.llm.provider_config import ProviderConfig

pytestmark = pytest.mark.integration


def test_ollama_chat_model_answers() -> None:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a concise assistant. Answer in one short sentence."),
            ("human", "{question}"),
        ]
    )
    chain = prompt | get_chat_model(ProviderConfig(provider="ollama")) | StrOutputParser()

    answer = chain.invoke({"question": "What is two plus two?"})

    assert "4" in answer or "four" in answer.lower()
