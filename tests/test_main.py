from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.main import app


def test_root(monkeypatch) -> None:
    container = MagicMock()
    monkeypatch.setattr("src.main.get_container", lambda: container)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "llm-service"
