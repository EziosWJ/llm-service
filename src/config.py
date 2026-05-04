from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_base_url: str
    llm_model: str
    llm_api_key: str | None = None
    llm_enable_thinking: bool = False
    embedding_model: str
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_prefix: str = "materials"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
