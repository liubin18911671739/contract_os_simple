"""
Configuration management for Contract OS Simple
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # ZhipuAI
    zhipu_api_key: Optional[str] = None  # Make optional for testing
    zhipu_chat_model: str = "glm-4-flash"
    zhipu_embed_model: str = "embedding-3"
    zhipu_rerank_model: str = "rerank-2"

    # Database
    database_path: str = "./data/database.db"

    # Storage
    storage_root: str = "./storage"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Concurrency
    max_concurrent_tasks: int = 3
    max_api_concurrent: int = 5

    # Rate Limiting
    enable_rate_limit: bool = True
    rate_limit_per_hour: int = 200  # Default rate limit per IP per hour


# Global settings instance
settings = Settings()


def get_storage_path(subpath: str = "") -> Path:
    """Get full path for storage"""
    base = Path(settings.storage_root)
    if subpath:
        return base / subpath
    return base


def get_db_path() -> Path:
    """Get database path"""
    return Path(settings.database_path)


def get_faissIndexPath() -> Path:
    """Get Faiss index directory path"""
    return Path("./data/faiss_indexes")
