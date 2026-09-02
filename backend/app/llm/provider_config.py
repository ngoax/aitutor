from typing import Literal, get_args

from pydantic import BaseModel, Field

ChatProvider = Literal["openai", "anthropic", "ollama", "nvidia", "azure"]

CHAT_PROVIDERS: tuple[ChatProvider, ...] = get_args(ChatProvider)

DEFAULT_PROVIDER: ChatProvider = "ollama"

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-5.4-mini",
    "anthropic": "claude-sonnet-5",
    "ollama": "gemma4:e2b",
    "nvidia": "nvidia/nemotron-3-ultra-550b-a55b",
    "azure": "gpt-5.6-luna",
}

StructuredMethod = Literal["json_schema", "function_calling", "json_mode"]

DEFAULT_STRUCTURED_METHOD: dict[str, StructuredMethod] = {
    "openai": "json_schema",
    "anthropic": "json_schema",
    # MLX builds silently drop native structured outputs and need
    # structured_method="function_calling"; GGUF builds honour json_schema.
    "ollama": "json_schema",
    "nvidia": "json_schema",
    "azure": "json_schema",
}


DEFAULT_TEMPERATURE: dict[str, float | None] = {
    "openai": 0.0,
    "anthropic": 0.0,
    "ollama": 0.0,
    "nvidia": 0.0,
    "azure": None, # reasoning models reject this param
}


class ProviderConfig(BaseModel):
    """Which chat model to use, and how it behaves."""

    provider: ChatProvider = DEFAULT_PROVIDER
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    structured_method: StructuredMethod | None = None

    def resolved_model(self) -> str:
        return self.model or DEFAULT_MODELS[self.provider]

    def resolved_temperature(self) -> float | None:
        if self.temperature is None:
            return DEFAULT_TEMPERATURE[self.provider]
        return self.temperature

    def resolved_structured_method(self) -> StructuredMethod:
        return self.structured_method or DEFAULT_STRUCTURED_METHOD[self.provider]
