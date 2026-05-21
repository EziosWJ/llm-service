"""Qdrant 向量数据库封装，负责集合管理、向量写入与检索。"""

from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

logger = logging.getLogger(__name__)


class QdrantStore:
    def __init__(self, url: str, collection_name: str, vector_size: int) -> None:
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.vector_size = vector_size

    def ensure_collection(self) -> None:
        """确保集合存在，并为 material_id 和 user_id 创建关键词索引以支持过滤查询。"""

        logger.info("Ensuring collection: %s", self.collection_name)
        if not self.client.collection_exists(self.collection_name):
            logger.info("Creating collection: %s (vector_size=%d)", self.collection_name, self.vector_size)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qm.VectorParams(size=self.vector_size, distance=qm.Distance.COSINE),
            )
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="material_id",
            field_schema=qm.PayloadSchemaType.KEYWORD,
            wait=True,
        )
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="user_id",
            field_schema=qm.PayloadSchemaType.KEYWORD,
            wait=True,
        )

    def upsert_points(self, points: list[qm.PointStruct]) -> None:
        """批量写入/更新向量点，空列表时跳过。"""

        if not points:
            return
        logger.debug("Upserting %d points to collection %s", len(points), self.collection_name)
        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        material_ids: list[str] | None = None,
        user_id: str | None = None,
    ) -> list[Any]:
        """按 query_vector 做相似度检索，支持按 material_ids / user_id 过滤。"""
        query_filter = self._build_filter(material_ids=material_ids, user_id=user_id)
        logger.debug("Qdrant search: top_k=%d, material_ids=%s, user_id=%s", top_k, material_ids, user_id)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        return list(response.points)

    def delete_by_material_id(self, material_id: str, user_id: str | None = None) -> int:
        """按 material_id 删除所有关联向量，返回删除数量。"""
        query_filter = self._build_filter(material_ids=[material_id], user_id=user_id)
        logger.debug("Deleting by material_id: %s, user_id=%s", material_id, user_id)
        count_before = self.client.count(
            collection_name=self.collection_name,
            count_filter=query_filter,
            exact=True,
        ).count
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qm.FilterSelector(filter=query_filter),
            wait=True,
        )
        logger.debug("Deleted %d points by material_id=%s", count_before, material_id)
        return count_before

    def _build_filter(
        self,
        material_ids: list[str] | None,
        user_id: str | None,
    ) -> qm.Filter | None:
        """组合 material_ids 和 user_id 条件为 Qdrant 过滤器，无条件时返回 None。"""
        conditions: list[qm.FieldCondition] = []
        if material_ids:
            conditions.append(
                qm.FieldCondition(
                    key="material_id",
                    match=qm.MatchAny(any=material_ids),
                )
            )
        if user_id:
            conditions.append(qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id)))

        if not conditions:
            return None
        return qm.Filter(must=conditions)
