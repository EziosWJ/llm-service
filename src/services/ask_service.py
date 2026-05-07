from __future__ import annotations

from src.infrastructure.llm_client import LLMClient
from src.models.responses import AskResponse, Source
from src.services.prompt_builder import PromptBuilder
from src.services.retriever import Retriever


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
                score=h.score,
            )
            for h in hits
        ]
        return AskResponse(answer=answer, sources=source_objs)
