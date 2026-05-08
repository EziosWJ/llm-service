from __future__ import annotations

from unittest.mock import MagicMock

from src.models.chunk import SourceChunk
from src.models.requests import GenerateRequest
from src.models.responses import GenerateResponse, Source
from src.services.generator import GeneratorService


def test_generate_consumes_source_chunk_attributes() -> None:
    retriever = MagicMock()
    prompt_builder = MagicMock()
    llm_client = MagicMock()
    retriever.search.return_value = [
        SourceChunk(text="chunk one", material_id="mat-1", chunk_index=3, score=0.9),
        SourceChunk(text="chunk two", material_id=None, score=None),
    ]
    prompt_builder.build_draft.return_value = "built prompt"
    llm_client.generate.return_value = "generated"

    service = GeneratorService(retriever, prompt_builder, llm_client)
    request = GenerateRequest(type="draft", topic="Topic", content="seed", material_ids=["mat-1"], user_id="u1")
    result = service.generate(request)

    assert isinstance(result, GenerateResponse)
    assert result.generated_text == "generated"
    assert result.sources == [
        Source(text="chunk one", material_id="mat-1", chunk_index=3, score=0.9),
        Source(text="chunk two", material_id=None, score=None),
    ]
    retriever.search.assert_called_once_with(
        query="Topic",
        material_ids=["mat-1"],
        user_id="u1",
        top_k=5,
    )
    prompt_builder.build_draft.assert_called_once_with("Topic", ["chunk one", "chunk two"], "seed")
    llm_client.generate.assert_called_once_with("built prompt")
