from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.main import app
from src.models.responses import AskResponse, Source


def _make_container(answer: str = "the answer", sources: list[Source] | None = None) -> MagicMock:
    if sources is None:
        sources = [Source(text="chunk one", material_id="mat-1", score=0.9)]
    container = MagicMock()
    container.ask_service.ask.return_value = AskResponse(answer=answer, sources=sources)
    return container


def test_ask_returns_200(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.ask.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post("/ask", json={"query": "What is X?", "user_id": "u1"})

    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "sources" in body
    assert body["answer"] == "the answer"
    assert len(body["sources"]) == 1
    assert body["sources"][0]["text"] == "chunk one"


def test_ask_passes_all_params(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.ask.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post(
        "/ask",
        json={
            "query": "What is X?",
            "material_ids": ["mat-1", "mat-2"],
            "user_id": "u1",
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    container.ask_service.ask.assert_called_once_with(
        query="What is X?",
        material_ids=["mat-1", "mat-2"],
        user_id="u1",
        top_k=5,
    )


def test_ask_empty_query_returns_400(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.ask.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post("/ask", json={"query": "", "user_id": "u1"})

    assert response.status_code == 400


def test_ask_missing_user_id_returns_400(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.ask.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post("/ask", json={"query": "What is X?"})

    assert response.status_code == 400


def test_ask_empty_material_ids_returns_400(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.ask.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post("/ask", json={"query": "What is X?", "user_id": "u1", "material_ids": []})

    assert response.status_code == 400
