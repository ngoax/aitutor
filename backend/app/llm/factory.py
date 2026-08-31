from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.llm.provider_config import ProviderConfig


def get_chat_model(config: ProviderConfig | None = None) -> BaseChatModel:
    config = config or ProviderConfig()
    model = config.resolved_model()

    if config.provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model, temperature=config.temperature, base_url=settings.ollama_base_url
        )
    if config.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model, temperature=config.temperature, api_key=settings.anthropic_api_key
        )
    if config.provider == "nvidia":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=config.temperature,
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
        )
    if config.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model, temperature=config.temperature, api_key=settings.openai_api_key
        )

    raise ValueError(f"Unknown LLM provider: {config.provider!r}")
