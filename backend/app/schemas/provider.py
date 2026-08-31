from pydantic import BaseModel

from app.llm.provider_config import ChatProvider, StructuredMethod


class ProviderInfo(BaseModel):
    provider: ChatProvider
    available: bool
    is_default: bool
    default_model: str
    structured_method: StructuredMethod
    detail: str | None = None
