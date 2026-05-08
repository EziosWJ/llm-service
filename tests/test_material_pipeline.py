from pathlib import Path
from types import SimpleNamespace

from qdrant_client.http import models as qm

from src.services.material_pipeline import MaterialPipeline


def test_process_file_replaces_existing_material_vectors(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("第一段\n\n第二段", encoding="utf-8")

    embedder = SimpleNamespace(embed_texts=lambda texts: [[0.1, 0.2, 0.3] for _ in texts])

    class FakeQdrantStore:
        def __init__(self) -> None:
            self.deleted: tuple[str, str | None] | None = None
            self.points: list[qm.PointStruct] = []

        def delete_by_material_id(self, material_id: str, user_id: str | None = None) -> int:
            self.deleted = (material_id, user_id)
            return 2

        def upsert_points(self, points: list[qm.PointStruct]) -> None:
            self.points = points

    qdrant_store = FakeQdrantStore()
    pipeline = MaterialPipeline(embedder=embedder, qdrant_store=qdrant_store)

    result = pipeline.process_file(file_path, material_id="mat-1", user_id="user-1")

    assert qdrant_store.deleted == ("mat-1", "user-1")
    assert result == {"deleted_count": 2, "chunk_count": 2}
    assert [point.payload["text"] for point in qdrant_store.points] == ["第一段", "第二段"]
    assert all(point.payload["material_id"] == "mat-1" for point in qdrant_store.points)
    assert all(point.payload["user_id"] == "user-1" for point in qdrant_store.points)
