from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/irvinbot_docs"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"

    # ── Embeddings ────────────────────────────────────────────────────────────
    # Opciones: ollama | openai
    EMBEDDING_PROVIDER: str = "ollama"
    EMBEDDING_MODEL: Optional[str] = None  # vacío = default del proveedor

    # ── Credenciales ─────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── Ollama ────────────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8004
    CHROMA_COLLECTION: str = "thesis_docs"

    UPLOAD_DIR: str = "/data/uploads"
    MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
