from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.main import app
from src.models.responses import GenerateResponse, Source


def _make_container() -> MagicMock:
    container = MagicMock()
    container.generator.generate.return_value = GenerateResponse(
        generated_text="generated",
        sources=[Source(text="chunk one", material_id="mat-1", chunk_index=2, score=0.9)],
    )
    return container


def test_generate_requires_user_id(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.generate.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post("/generate", json={"type": "draft", "topic": "Topic"})

    assert response.status_code == 400


def test_generate_rejects_empty_material_ids(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.generate.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post(
        "/generate",
        json={"type": "draft", "topic": "Topic", "user_id": "u1", "material_ids": []},
    )

    assert response.status_code == 400


def test_generate_returns_chunk_index(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.generate.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post("/generate", json={"type": "draft", "topic": "Topic", "user_id": "u1"})

    assert response.status_code == 200
    assert response.json()["sources"][0]["chunk_index"] == 2
