import httpx
from fastapi import APIRouter

from app.core.config import settings
from app.llm.provider_config import CHAT_PROVIDERS, ChatProvider, ProviderConfig
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
                default_model=config.resolved_model(),
                supports_tool_calling=config.resolved_tool_calling(),
                detail=detail,
            )
        )
    return infos
