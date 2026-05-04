from __future__ import annotations

from typing import Any

from src.infrastructure.qdrant import QdrantStore
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
    ) -> list[dict[str, Any]]:
        vector = self.embedder.embed_texts([query])[0]
        points = self.qdrant_store.search(
            query_vector=vector,
            top_k=top_k,
            material_ids=material_ids,
            user_id=user_id,
        )
        results: list[dict[str, Any]] = []
        for point in points:
            payload = point.payload or {}
            results.append(
                {
                    "text": payload.get("text", ""),
                    "score": float(point.score),
                    "metadata": payload,
                }
            )
        return results
