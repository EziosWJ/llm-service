from fastapi.testclient import TestClient

from src.main import app


def test_health_default_skips_llm(monkeypatch) -> None:
    class DummyQdrantClient:
        def get_collection(self, _: str):
            class _Resp:
                status = "green"

            return _Resp()

    class DummyStore:
        collection_name = "materials_dummy"
        client = DummyQdrantClient()

        def ensure_collection(self) -> None:
            return None

    class DummyLLM:
        def generate(self, _: str) -> str:
            raise AssertionError("should not be called when deep=false")

    class DummyContainer:
        qdrant_store = DummyStore()
        llm_client = DummyLLM()

    monkeypatch.setattr("src.api.health.get_container", lambda: DummyContainer())
    monkeypatch.setattr("src.main.get_container", lambda: DummyContainer())
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"]["llm"]["status"] == "skipped"
