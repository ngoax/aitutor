from langchain_core.embeddings import Embeddings

DEFAULT_PROVIDER = "huggingface"
DEFAULT_MODELS = {
    "huggingface": "sentence-transformers/all-MiniLM-L6-v2",
    "ollama": "nomic-embed-text",
    "openai": "text-embedding-3-small",
}


def get_embedding_model(provider: str | None = None, model: str | None = None) -> Embeddings:
    provider = provider or DEFAULT_PROVIDER
    model = model or DEFAULT_MODELS.get(provider)

    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=model)

    if provider == "ollama":
        raise NotImplementedError("ollama embeddings: use OllamaEmbeddings(model=model)")
    if provider == "openai":
        raise NotImplementedError("openai embeddings: use OpenAIEmbeddings(model=model)")

    raise ValueError(f"Unknown embedding provider: {provider!r}")
