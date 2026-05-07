from __future__ import annotations

from src.infrastructure.qdrant import QdrantStore
from src.models.chunk import SourceChunk
from src.services.embedder import Embedder


class Retriever:
    def __init__(self, embedder: Embedder, qdrant_store: QdrantStore) -> None:
        self.embedder = embedder
        self.qdrant_store = qdrant_store

    def search(
        self,
        query: str,
        material_ids: list[str] | None = None,
        user_id: str | None = None,
        top_k: int = 5,
    ) -> list[SourceChunk]:
        vector = self.embedder.embed_texts([query])[0]
        points = self.qdrant_store.search(
            query_vector=vector,
            top_k=top_k,
            material_ids=material_ids,
            user_id=user_id,
        )
        results: list[SourceChunk] = []
        for point in points:
            payload = point.payload or {}
            text = payload.get("text")
            if not isinstance(text, str):
                continue
            if not text.strip():
                continue

            score = getattr(point, "score", None)
            results.append(
                SourceChunk(
                    text=text,
                    material_id=payload.get("material_id"),
                    score=float(score) if score is not None else None,
                )
            )
        return results
