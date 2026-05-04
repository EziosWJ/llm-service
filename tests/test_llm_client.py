import pytest

from src.infrastructure import llm_client
from src.models.errors import UpstreamError


def test_llm_client_init_uses_config_and_default_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(llm_client, "OpenAI", FakeOpenAI)

    client = llm_client.LLMClient(
        base_url="https://example.com/v1",
        model="gpt-4.1-mini",
        api_key="test-key",
    )

    assert client.model == "gpt-4.1-mini"
    assert captured["base_url"] == "https://example.com/v1"
    assert captured["api_key"] == "test-key"
    assert captured["timeout"] == 60.0


def test_generate_returns_output_text(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeMessage:
        content = "hello"

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        @staticmethod
        def create(**kwargs):
            assert kwargs["model"] == "gpt-4.1-mini"
            assert kwargs["messages"] == [{"role": "user", "content": "hi"}]
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm_client, "OpenAI", FakeOpenAI)

    client = llm_client.LLMClient(
        base_url="https://example.com/v1",
        model="gpt-4.1-mini",
        api_key="test-key",
    )

    assert client.generate("hi") == "hello"


@pytest.mark.parametrize("error_attr", ["APITimeoutError", "APIConnectionError"])
def test_generate_maps_upstream_errors(monkeypatch: pytest.MonkeyPatch, error_attr: str) -> None:
    class FakeUpstreamError(Exception):
        pass

    class FakeCompletions:
        @staticmethod
        def create(**kwargs):
            raise FakeUpstreamError("upstream down")

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm_client, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(llm_client, error_attr, FakeUpstreamError)

    client = llm_client.LLMClient(
        base_url="https://example.com/v1",
        model="gpt-4.1-mini",
        api_key="test-key",
    )

    with pytest.raises(UpstreamError):
        client.generate("hi")

