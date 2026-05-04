from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm


class QdrantStore:
    def __init__(self, url: str, collection_name: str, vector_size: int) -> None:
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.vector_size = vector_size

    def ensure_collection(self) -> None:
        if not self.client.collection_exists(self.collection_name):
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
        if not points:
            return
        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        material_ids: list[str] | None = None,
        user_id: str | None = None,
    ) -> list[Any]:
        query_filter = self._build_filter(material_ids=material_ids, user_id=user_id)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        return list(response.points)

    def delete_by_material_id(self, material_id: str, user_id: str | None = None) -> int:
        query_filter = self._build_filter(material_ids=[material_id], user_id=user_id)
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
        return count_before

    def _build_filter(
        self,
        material_ids: list[str] | None,
        user_id: str | None,
    ) -> qm.Filter | None:
        conditions: list[qm.FieldCondition] = []
        if material_ids:
            conditions.append(
                qm.FieldCondition(
                    key="material_id",
                    match=qm.MatchAny(any=material_ids),
                )
            )
        elif user_id:
            conditions.append(qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id)))

        if not conditions:
            return None
        return qm.Filter(must=conditions)
