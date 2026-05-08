from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.main import app


def _make_container() -> MagicMock:
    container = MagicMock()
    container.material_pipeline.process_file.return_value = {"deleted_count": 1, "chunk_count": 2}
    container.qdrant_store.delete_by_material_id.return_value = 3
    return container


def test_process_material_returns_replacement_counts(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.materials.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post(
        "/materials/process",
        files={"file": ("sample.txt", b"hello", "text/plain")},
        data={"material_id": "mat-1", "user_id": "u1"},
    )

    assert response.status_code == 200
    assert response.json() == {"deleted_count": 1, "chunk_count": 2}


def test_process_material_rejects_unsupported_file_type(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.materials.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post(
        "/materials/process",
        files={"file": ("sample.csv", b"a,b", "text/csv")},
        data={"material_id": "mat-1", "user_id": "u1"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "validation_error"


def test_delete_vectors_requires_user_id(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.materials.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.delete("/materials/mat-1/vectors")

    assert response.status_code == 400


def test_delete_vectors_scopes_by_user_id(monkeypatch) -> None:
    container = _make_container()
    monkeypatch.setattr("src.api.materials.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.delete("/materials/mat-1/vectors?user_id=u1")

    assert response.status_code == 200
    assert response.json() == {"deleted_count": 3}
    container.qdrant_store.delete_by_material_id.assert_called_once_with("mat-1", user_id="u1")
