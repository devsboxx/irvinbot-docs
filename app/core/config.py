from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/irvinbot_docs"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"

    UPLOAD_DIR: str = "/data/uploads"
    MAX_FILE_SIZE_MB: int = 50

    # Cloudflare R2
    R2_ENDPOINT: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "irvinbot"
    R2_PUBLIC_URL: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
