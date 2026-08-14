import os
from typing import List, Union
from pydantic import AnyHttpUrl, BeforeValidator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

def parse_cors(v: str) -> Union[List[str], str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )
    
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/sara_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    JWT_SECRET: str = "super_secret_jwt_key_change_me_in_production"
    GEMINI_API_KEY: str = ""
    
    CORS_ORIGINS: Annotated[
        Union[List[str], str], BeforeValidator(parse_cors)
    ] = ["http://localhost:5173", "http://localhost:3000"]
    
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"
    COOKIE_SECURE: bool = False
    
    # AI Pipeline Settings
    AI_TIMEOUT_SECONDS: int = 10
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.80

    # Evidence & Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_EVIDENCE_SIZE_MB: int = 10
    ALLOWED_EVIDENCE_MIME_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf",
        "video/mp4",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    @model_validator(mode="before")
    @classmethod
    def set_cookie_secure(cls, data: dict) -> dict:
        env = data.get("ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
        if "COOKIE_SECURE" not in data:
            data["COOKIE_SECURE"] = env == "production"
        return data

settings = Settings()
