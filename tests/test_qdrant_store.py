from types import SimpleNamespace

from src.infrastructure import qdrant


def test_search_uses_query_points(monkeypatch) -> None:
    captured = {}

    class FakeClient:
        def query_points(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(points=[SimpleNamespace(payload={"text": "hit"}, score=0.9)])

    monkeypatch.setattr(qdrant, "QdrantClient", lambda url: FakeClient())

    store = qdrant.QdrantStore(url="http://localhost:6333", collection_name="materials_test", vector_size=3)
    results = store.search([0.1, 0.2, 0.3], top_k=2, material_ids=["mat-001"], user_id="user-001")

    assert captured["collection_name"] == "materials_test"
    assert captured["query"] == [0.1, 0.2, 0.3]
    assert captured["limit"] == 2
    assert captured["with_payload"] is True
    assert results[0].payload["text"] == "hit"
    assert results[0].score == 0.9
