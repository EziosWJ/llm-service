from src.config import Settings


def test_settings_read_env(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:9000/v1")
    monkeypatch.setenv("LLM_MODEL", "mock-model")
    monkeypatch.setenv("EMBEDDING_MODEL", "mock-embedding")
    settings = Settings()
    assert settings.llm_base_url == "http://localhost:9000/v1"
    assert settings.llm_model == "mock-model"
    assert settings.embedding_model == "mock-embedding"
