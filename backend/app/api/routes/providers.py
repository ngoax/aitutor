import httpx
from fastapi import APIRouter

from app.core.config import settings
from app.llm.provider_config import (
    CHAT_PROVIDERS,
    DEFAULT_MODELS,
    DEFAULT_PROVIDER,
    ChatProvider,
    ProviderConfig,
)
from app.schemas.provider import ProviderInfo

router = APIRouter(prefix="/providers", tags=["providers"])


def _ollama_models() -> list[str] | None:
    try:
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0)
        if response.status_code != 200:
            return None
        return [m["name"] for m in response.json().get("models", [])]
    except Exception:
        return None


def _availability(provider: ChatProvider) -> tuple[bool, str | None]:
    if provider == "openai":
        if settings.openai_api_key is None:
            return False, "No OPENAI_API_KEY set in backend/.env"
        return True, None

    if provider == "anthropic":
        if settings.anthropic_api_key is None:
            return False, "No ANTHROPIC_API_KEY set in backend/.env"
        return True, None

    if provider == "nvidia":
        if settings.nvidia_api_key is None:
            return False, "No NVIDIA_API_KEY set in backend/.env"
        return True, f"Key set, using {DEFAULT_MODELS['nvidia']} (not verified until generation)"

    if provider == "azure":
        if settings.azure_api_key is None:
            return False, "No AZURE_API_KEY set in backend/.env"
        if settings.azure_endpoint is None:
            return False, "No AZURE_ENDPOINT set in backend/.env"
        return True, f"Deployment {DEFAULT_MODELS['azure']} at {settings.azure_endpoint}"

    if provider == "ollama":
        models = _ollama_models()
        if models is None:
            return False, f"Ollama not reachable at {settings.ollama_base_url}"
        if not models:
            return (
                False,
                "Ollama is running but no models are pulled (e.g try: ollama pull llama3.1)",
            )
        return True, f"Installed models: {', '.join(models)}"

    return False, "Unknown provider"


@router.get("", response_model=list[ProviderInfo])
def list_providers() -> list[ProviderInfo]:
    infos: list[ProviderInfo] = []
    for provider in CHAT_PROVIDERS:
        available, detail = _availability(provider)
        config = ProviderConfig(provider=provider)
        infos.append(
            ProviderInfo(
                provider=provider,
                available=available,
                is_default=provider == DEFAULT_PROVIDER,
                default_model=config.resolved_model(),
                structured_method=config.resolved_structured_method(),
                detail=detail,
            )
        )
    return infos
