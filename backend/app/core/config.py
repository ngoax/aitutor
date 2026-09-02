from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: Path = REPO_ROOT / "data"
    cors_origins: list[str] = ["http://localhost:5173"]

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    nvidia_api_key: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    azure_api_key: str | None = None
    azure_endpoint: str | None = None
    # Structured outputs need a recent api-version; remove if model rejects this
    azure_api_version: str = "2024-10-21"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'aitutor.db'}"


settings = Settings()
