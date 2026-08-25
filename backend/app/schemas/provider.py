from pydantic import BaseModel

from app.llm.provider_config import ChatProvider, StructuredMethod


class ProviderInfo(BaseModel):
    provider: ChatProvider
    available: bool
    default_model: str
    structured_method: StructuredMethod | None = None
    detail: str | None = None
