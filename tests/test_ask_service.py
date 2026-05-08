from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.models.chunk import SourceChunk
from src.models.responses import AskResponse, Source
from src.services.ask_service import AskService


@pytest.fixture()
def mock_deps() -> tuple[MagicMock, MagicMock, MagicMock]:
    retriever = MagicMock()
    prompt_builder = MagicMock()
    llm_client = MagicMock()
    return retriever, prompt_builder, llm_client


def _make_hit(text: str, material_id: str | None, score: float | None, chunk_index: int | None = None) -> SourceChunk:
    return SourceChunk(text=text, material_id=material_id, chunk_index=chunk_index, score=score)


class TestAskService:
    def test_ask_returns_answer_and_sources(self, mock_deps: tuple[MagicMock, MagicMock, MagicMock]) -> None:
        retriever, prompt_builder, llm_client = mock_deps

        hits = [
            _make_hit("chunk one", "mat-1", 0.9, chunk_index=1),
            _make_hit("chunk two", "mat-2", 0.8),
        ]
        retriever.search.return_value = hits
        prompt_builder.build_ask.return_value = "built prompt"
        llm_client.generate.return_value = "the answer"

        service = AskService(retriever, prompt_builder, llm_client)
        result = service.ask(query="What is X?", material_ids=["mat-1", "mat-2"], user_id="u1", top_k=3)

        assert isinstance(result, AskResponse)
        assert result.answer == "the answer"
        assert len(result.sources) == 2

        retriever.search.assert_called_once_with(
            query="What is X?",
            material_ids=["mat-1", "mat-2"],
            user_id="u1",
            top_k=3,
        )
        prompt_builder.build_ask.assert_called_once_with("What is X?", ["chunk one", "chunk two"])
        llm_client.generate.assert_called_once_with("built prompt")

    def test_sources_mapped_correctly(self, mock_deps: tuple[MagicMock, MagicMock, MagicMock]) -> None:
        retriever, prompt_builder, llm_client = mock_deps

        hits = [
            _make_hit("text A", "m-10", 0.95),
            _make_hit("text B", "m-20", 0.85),
            _make_hit("text C", "m-30", 0.75),
        ]
        retriever.search.return_value = hits
        prompt_builder.build_ask.return_value = "prompt"
        llm_client.generate.return_value = "answer"

        service = AskService(retriever, prompt_builder, llm_client)
        result = service.ask(query="test", top_k=3)

        expected_sources = [
            Source(text="text A", material_id="m-10", score=0.95),
            Source(text="text B", material_id="m-20", score=0.85),
            Source(text="text C", material_id="m-30", score=0.75),
        ]
        assert result.sources == expected_sources

    def test_ask_defaults(self, mock_deps: tuple[MagicMock, MagicMock, MagicMock]) -> None:
        retriever, prompt_builder, llm_client = mock_deps

        retriever.search.return_value = []
        prompt_builder.build_ask.return_value = "prompt"
        llm_client.generate.return_value = "answer"

        service = AskService(retriever, prompt_builder, llm_client)
        result = service.ask(query="hello", user_id="u1")

        assert isinstance(result, AskResponse)
        retriever.search.assert_called_once_with(
            query="hello",
            material_ids=None,
            user_id="u1",
            top_k=3,
        )
