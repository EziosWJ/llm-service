"""素材处理管线：文件上传后的完整处理流程——解析文档、分块、向量化、存入 Qdrant。"""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from qdrant_client.http import models as qm

from src.infrastructure.qdrant import QdrantStore
from src.services.chunker import chunk_text
from src.services.document_parser import parse_document
from src.services.embedder import Embedder

logger = logging.getLogger(__name__)


class MaterialPipeline:
    def __init__(self, embedder: Embedder, qdrant_store: QdrantStore) -> None:
        self.embedder = embedder
        self.qdrant_store = qdrant_store

    def process_file(self, file_path: str | Path, material_id: str, user_id: str) -> dict[str, int]:
        """处理单个素材文件：删除旧数据 -> 解析 -> 分块 -> 向量化 -> 写入向量库。"""
        logger.info("Processing file: material_id=%s, user_id=%s, path=%s", material_id, user_id, file_path)
        deleted_count = self.qdrant_store.delete_by_material_id(material_id, user_id=user_id)
        parsed = parse_document(file_path)
        sections = parsed.get("sections", [])
        section_title = sections[0]["heading"] if sections else None
        chunks = chunk_text(
            parsed.get("text", ""),
            metadata={
                "material_id": material_id,
                "user_id": user_id,
                "section_title": section_title,
            },
        )
        vectors = self.embedder.embed_texts([c.text for c in chunks])
        points: list[qm.PointStruct] = []
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False)):
            payload = dict(chunk.metadata)
            payload.update({"chunk_index": idx, "text": chunk.text})
            points.append(
                qm.PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload=payload,
                )
            )
        self.qdrant_store.upsert_points(points)
        logger.info("File processed: material_id=%s, deleted=%d, chunks=%d", material_id, deleted_count, len(points))
        return {"deleted_count": deleted_count, "chunk_count": len(points)}
