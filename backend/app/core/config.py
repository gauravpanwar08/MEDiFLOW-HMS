from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "MediCore HMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://hms_user:hms_pass@localhost:5432/hms_db"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://hms_user:hms_pass@localhost:5432/hms_db"

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    ANTHROPIC_API_KEY: str = ""

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    DEFAULT_HOSPITAL_SLUG: str = "default"


settings = Settings()
