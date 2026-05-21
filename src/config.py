# 应用配置：从 .env 文件和环境变量读取配置项，全局单例缓存

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，字段自动从环境变量或 .env 文件绑定"""
    llm_base_url: str
    llm_model: str
    llm_api_key: str | None = None
    llm_enable_thinking: bool = False
    embedding_model: str
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_prefix: str = "materials"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """全局单例：确保整个进程只解析一次配置"""
    return Settings()
