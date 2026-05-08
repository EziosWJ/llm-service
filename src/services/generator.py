from __future__ import annotations

from src.infrastructure.llm_client import LLMClient
from src.models.requests import GenerateRequest
from src.models.responses import GenerateResponse, Source
from src.services.prompt_builder import PromptBuilder
from src.services.retriever import Retriever


class GeneratorService:
    def __init__(
        self,
        retriever: Retriever,
        prompt_builder: PromptBuilder,
        llm_client: LLMClient,
    ) -> None:
        self.retriever = retriever
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client

    def generate(self, request: GenerateRequest) -> GenerateResponse:
        hits = self.retriever.search(
            query=request.topic,
            material_ids=request.material_ids,
            user_id=request.user_id,
            top_k=request.top_k,
        )
        sources = [h.text for h in hits]
        if request.type == "outline":
            prompt = self.prompt_builder.build_outline(request.topic, sources, request.content or "")
        elif request.type == "draft":
            prompt = self.prompt_builder.build_draft(request.topic, sources, request.content or "")
        elif request.type == "polished":
            prompt = self.prompt_builder.build_polished(request.topic, sources, request.content or "")
        else:
            prompt = self.prompt_builder.build_title(request.topic, sources, request.content or "")

        generated = self.llm_client.generate(prompt)
        source_objs = [
            Source(
                text=h.text,
                material_id=h.material_id,
                chunk_index=h.chunk_index,
                score=h.score,
            )
            for h in hits
        ]
        return GenerateResponse(generated_text=generated, sources=source_objs)
