from typing import Literal, get_args

from pydantic import BaseModel, Field

ChatProvider = Literal["openai", "anthropic", "ollama"]

# Derived from the Literal so providers have exactly one definition.
CHAT_PROVIDERS: tuple[ChatProvider, ...] = get_args(ChatProvider)

DEFAULT_PROVIDER: ChatProvider = "ollama"

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-5",
    "anthropic": "claude-sonnet-5",
    "ollama": "gemma4:e2b-mlx",
}

DEFAULT_SUPPORTS_TOOL_CALLING: dict[str, bool] = {
    "openai": True,
    "anthropic": True,
    # Ollama tool calling works only via method="function_calling"
    # (default json_schema path fails to parse on small models)
    "ollama": True,
}


class ProviderConfig(BaseModel):
    """Which chat model to use, and how it behaves."""

    provider: ChatProvider = DEFAULT_PROVIDER
    model: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    supports_tool_calling: bool | None = None

    def resolved_model(self) -> str:
        return self.model or DEFAULT_MODELS[self.provider]

    def resolved_tool_calling(self) -> bool:
        if self.supports_tool_calling is not None:
            return self.supports_tool_calling
        return DEFAULT_SUPPORTS_TOOL_CALLING[self.provider]
