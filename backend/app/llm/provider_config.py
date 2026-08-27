from typing import Literal, get_args

from pydantic import BaseModel, Field

ChatProvider = Literal["openai", "anthropic", "ollama", "nvidia"]

# Derived from the Literal so providers have exactly one definition.
CHAT_PROVIDERS: tuple[ChatProvider, ...] = get_args(ChatProvider)

DEFAULT_PROVIDER: ChatProvider = "ollama"

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-5.4-mini",
    "anthropic": "claude-sonnet-5",
    "ollama": "gemma4:e2b",
    "nvidia": "openai/gpt-oss-20b",
}

StructuredMethod = Literal["json_schema", "function_calling", "json_mode"]

# None means the integration chooses for itself and rejects an explicit method.
DEFAULT_STRUCTURED_METHOD: dict[str, StructuredMethod | None] = {
    "openai": "json_schema",
    "anthropic": "json_schema",
    # MLX builds silently drop native structured outputs and need
    # structured_method="function_calling"; GGUF builds honour json_schema.
    "ollama": "json_schema",
    # ChatNVIDIA warns that method is unnecessary and ignores it.
    "nvidia": None,
}


class ProviderConfig(BaseModel):
    """Which chat model to use, and how it behaves."""

    provider: ChatProvider = DEFAULT_PROVIDER
    model: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    structured_method: StructuredMethod | None = None

    def resolved_model(self) -> str:
        return self.model or DEFAULT_MODELS[self.provider]

    def resolved_structured_method(self) -> StructuredMethod | None:
        return self.structured_method or DEFAULT_STRUCTURED_METHOD[self.provider]
