"""向量检索服务：将查询文本向量化后，在 Qdrant 中按相似度搜索匹配的素材片段。"""

from __future__ import annotations

import logging

from src.infrastructure.qdrant import QdrantStore
from src.models.chunk import SourceChunk
from src.services.embedder import Embedder

logger = logging.getLogger(__name__)


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
        """执行向量检索，支持按 material_ids 和 user_id 过滤，返回 top_k 个最相关的片段。"""
        logger.debug("Vector search: query=%s, material_ids=%s, user_id=%s, top_k=%d", query[:50], material_ids, user_id, top_k)
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
            chunk_index = payload.get("chunk_index")
            results.append(
                SourceChunk(
                    text=text,
                    material_id=payload.get("material_id"),
                    chunk_index=chunk_index if isinstance(chunk_index, int) else None,
                    score=float(score) if score is not None else None,
                )
            )
        logger.debug("Search returned %d results", len(results))
        return results
