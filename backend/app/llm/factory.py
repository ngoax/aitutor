from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.llm.provider_config import ProviderConfig


def get_chat_model(config: ProviderConfig | None = None) -> BaseChatModel:
    config = config or ProviderConfig()
    model = config.resolved_model()
    temperature = config.resolved_temperature()
    # Left out entirely when None, since some models reject the parameter.
    options: dict = {} if temperature is None else {"temperature": temperature}

    if config.provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model, **options, base_url=settings.ollama_base_url)
    if config.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, **options, api_key=settings.anthropic_api_key)
    if config.provider == "nvidia":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            **options,
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
        )
    if config.provider == "azure":
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_deployment=model,
            **options,
            api_key=settings.azure_api_key,
            azure_endpoint=settings.azure_endpoint,
            api_version=settings.azure_api_version,
        )
    if config.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, **options, api_key=settings.openai_api_key)

    raise ValueError(f"Unknown LLM provider: {config.provider!r}")
