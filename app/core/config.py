from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/irvinbot_docs"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"

    UPLOAD_DIR: str = "/data/uploads"
    MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
