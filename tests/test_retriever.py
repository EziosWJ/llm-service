from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.models.chunk import SourceChunk
from src.services.retriever import Retriever


def test_search_maps_qdrant_payload_to_source_chunks() -> None:
    embedder = MagicMock()
    qdrant_store = MagicMock()
    embedder.embed_texts.return_value = [[0.1, 0.2, 0.3]]
    qdrant_store.search.return_value = [
        SimpleNamespace(
            payload={"text": "chunk one", "material_id": "mat-1", "chunk_index": 7, "ignored": "secret"},
            score=0.9,
        )
    ]

    retriever = Retriever(embedder=embedder, qdrant_store=qdrant_store)
    results = retriever.search(query="What is X?", material_ids=["mat-1"], user_id="u1", top_k=3)

    assert results == [SourceChunk(text="chunk one", material_id="mat-1", chunk_index=7, score=0.9)]
    embedder.embed_texts.assert_called_once_with(["What is X?"])
    qdrant_store.search.assert_called_once_with(
        query_vector=[0.1, 0.2, 0.3],
        top_k=3,
        material_ids=["mat-1"],
        user_id="u1",
    )


def test_search_skips_empty_text_hits_and_preserves_remaining_order() -> None:
    embedder = MagicMock()
    qdrant_store = MagicMock()
    embedder.embed_texts.return_value = [[0.1]]
    qdrant_store.search.return_value = [
        SimpleNamespace(payload={"text": "first", "material_id": "mat-1"}, score=0.9),
        SimpleNamespace(payload={"text": "", "material_id": "mat-empty"}, score=0.8),
        SimpleNamespace(payload={"text": "   ", "material_id": "mat-blank"}, score=0.7),
        SimpleNamespace(payload={"text": "second", "material_id": "mat-2"}, score=0.6),
    ]

    retriever = Retriever(embedder=embedder, qdrant_store=qdrant_store)
    results = retriever.search(query="query")

    assert results == [
        SourceChunk(text="first", material_id="mat-1", score=0.9),
        SourceChunk(text="second", material_id="mat-2", score=0.6),
    ]


def test_search_skips_non_string_text_hits() -> None:
    embedder = MagicMock()
    qdrant_store = MagicMock()
    embedder.embed_texts.return_value = [[0.1]]
    qdrant_store.search.return_value = [
        SimpleNamespace(payload={"text": 123, "material_id": "mat-number"}, score=0.9),
        SimpleNamespace(payload={"text": ["not", "text"], "material_id": "mat-list"}, score=0.8),
        SimpleNamespace(payload={"text": "real text", "material_id": "mat-1"}, score=0.7),
    ]

    retriever = Retriever(embedder=embedder, qdrant_store=qdrant_store)
    results = retriever.search(query="query")

    assert results == [SourceChunk(text="real text", material_id="mat-1", score=0.7)]


def test_search_tolerates_missing_material_id_and_score() -> None:
    embedder = MagicMock()
    qdrant_store = MagicMock()
    embedder.embed_texts.return_value = [[0.1]]
    qdrant_store.search.return_value = [
        SimpleNamespace(payload={"text": "without material"}),
        SimpleNamespace(payload={"text": "without score", "material_id": "mat-2"}),
    ]

    retriever = Retriever(embedder=embedder, qdrant_store=qdrant_store)
    results = retriever.search(query="query")

    assert results == [
        SourceChunk(text="without material", material_id=None, score=None),
        SourceChunk(text="without score", material_id="mat-2", score=None),
    ]
