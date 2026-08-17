from pydantic import BaseModel

from app.llm.provider_config import ChatProvider


class ProviderInfo(BaseModel):
    provider: ChatProvider
    available: bool
    default_model: str
    supports_tool_calling: bool
    detail: str | None = None
