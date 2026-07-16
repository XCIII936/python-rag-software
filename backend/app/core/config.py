"""Application configuration via environment variables."""

import os
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Course Teaching Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./course_teaching_agent.db"

    # JWT
    SECRET_KEY: str = "change-me-in-production-use-a-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "course_document_chunks"

    # DashScope (Qwen)
    DASHSCOPE_API_KEY: Optional[str] = None
    LLM_MODEL: str = "qwen3-max"
    EMBEDDING_MODEL: str = "text-embedding-v3"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # File upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list[str] = [
        ".pdf", ".ppt", ".pptx", ".doc", ".docx", ".md", ".markdown"
    ]

    @model_validator(mode="after")
    def resolve_api_key(self) -> "Settings":
        """Prefer system env `ali-qwen3-max-api` over DASHSCOPE_API_KEY / .env."""
        system_key = os.environ.get("ali-qwen3-max-api")
        if system_key:
            self.DASHSCOPE_API_KEY = system_key
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
