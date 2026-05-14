from __future__ import annotations

import logging
from typing import Iterator

from src.infrastructure.llm_client import LLMClient
from src.models.errors import UpstreamError
from src.models.responses import AskResponse, Source
from src.services.prompt_builder import PromptBuilder
from src.services.retriever import Retriever

logger = logging.getLogger(__name__)


class AskService:
    def __init__(
        self,
        retriever: Retriever,
        prompt_builder: PromptBuilder,
        llm_client: LLMClient,
    ) -> None:
        self.retriever = retriever
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client

    def ask(
        self,
        query: str,
        material_ids: list[str] | None = None,
        user_id: str | None = None,
        top_k: int = 3,
    ) -> AskResponse:
        logger.info("Ask: query=%s, material_ids=%s, top_k=%d", query[:50], material_ids, top_k)
        hits = self.retriever.search(
            query=query,
            material_ids=material_ids,
            user_id=user_id,
            top_k=top_k,
        )
        source_texts = [h.text for h in hits]
        prompt = self.prompt_builder.build_ask(query, source_texts)
        answer = self.llm_client.generate(prompt)
        source_objs = [
            Source(
                text=h.text,
                material_id=h.material_id,
                chunk_index=h.chunk_index,
                score=h.score,
            )
            for h in hits
        ]
        logger.info("Ask completed: answer_length=%d, sources=%d", len(answer), len(source_objs))
        return AskResponse(answer=answer, sources=source_objs)

    def ask_stream(
        self,
        query: str,
        material_ids: list[str] | None = None,
        user_id: str | None = None,
        top_k: int = 3,
    ) -> Iterator[dict]:
        logger.info("Ask stream: query=%s, material_ids=%s, top_k=%d", query[:50], material_ids, top_k)
        hits = self.retriever.search(
            query=query,
            material_ids=material_ids,
            user_id=user_id,
            top_k=top_k,
        )
        source_texts = [h.text for h in hits]
        prompt = self.prompt_builder.build_ask(query, source_texts)

        sources = [
            {
                "text": h.text,
                "material_id": h.material_id,
                "chunk_index": h.chunk_index,
                "score": h.score,
            }
            for h in hits
        ]
        yield {"event": "sources", "data": sources}

        try:
            for chunk in self.llm_client.generate_stream(prompt):
                yield {"event": "delta", "data": {"text": chunk}}
        except UpstreamError as exc:
            logger.error("Ask stream upstream error: %s", exc.detail)
            yield {"event": "error", "data": {"detail": exc.detail}}
            return

        yield {"event": "done", "data": {}}
        logger.info("Ask stream completed: sources=%d", len(sources))
