"""
Embedding provider factory para irvinbot-docs.

EMBEDDING_PROVIDER | Modelo por defecto         | API key requerida
-------------------|----------------------------|------------------
ollama             | nomic-embed-text           | no (local)
openai             | text-embedding-3-small     | OPENAI_API_KEY

Para cambiar de proveedor basta con ajustar EMBEDDING_PROVIDER en el .env.
"""

from langchain_core.embeddings import Embeddings
from app.core.config import settings

_EMBEDDING_DEFAULTS: dict[str, str] = {
    "ollama": "nomic-embed-text",
    "openai": "text-embedding-3-small",
}


def get_embeddings() -> Embeddings:
    """Return a LangChain embeddings model for the configured provider."""
    provider = settings.EMBEDDING_PROVIDER.lower()
    model = settings.EMBEDDING_MODEL or _EMBEDDING_DEFAULTS.get(provider)

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model=model, base_url=settings.OLLAMA_BASE_URL)

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=model, api_key=settings.OPENAI_API_KEY)

    raise ValueError(
        f"EMBEDDING_PROVIDER '{provider}' no reconocido. "
        "Opciones: ollama, openai"
    )
