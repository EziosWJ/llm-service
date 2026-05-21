"""内容生成服务：根据请求类型（outline/draft/polished/title）检索素材并调用 LLM 生成内容。"""

from __future__ import annotations

import logging
from typing import Iterator

from src.infrastructure.llm_client import LLMClient
from src.models.errors import UpstreamError
from src.models.requests import GenerateRequest
from src.models.responses import GenerateResponse, Source
from src.services.prompt_builder import PromptBuilder
from src.services.retriever import Retriever

logger = logging.getLogger(__name__)


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
        """同步生成：检索素材 -> 根据 type 选择对应 prompt 模板 -> LLM 生成 -> 返回结果。"""
        hits = self.retriever.search(
            query=request.topic,
            material_ids=request.material_ids,
            user_id=request.user_id,
            top_k=request.top_k,
        )
        sources = [h.text for h in hits]
        logger.info("Generate: topic=%s, type=%s, source_count=%d", request.topic[:50], request.type, len(sources))
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
        logger.info("Generate completed: text_length=%d", len(generated))
        return GenerateResponse(generated_text=generated, sources=source_objs)

    def generate_stream(self, request: GenerateRequest) -> Iterator[dict]:
        """流式生成：依次 yield sources -> delta（逐 token）-> done 事件，供 SSE 消费。"""
        hits = self.retriever.search(
            query=request.topic,
            material_ids=request.material_ids,
            user_id=request.user_id,
            top_k=request.top_k,
        )
        sources = [h.text for h in hits]
        logger.info("GenerateStream: topic=%s, type=%s, source_count=%d", request.topic[:50], request.type, len(sources))

        # yield sources 事件
        source_dicts = [
            {
                "text": h.text,
                "material_id": h.material_id,
                "chunk_index": h.chunk_index,
                "score": h.score,
            }
            for h in hits
        ]
        yield {"event": "sources", "data": source_dicts}

        # 构建 prompt
        if request.type == "outline":
            prompt = self.prompt_builder.build_outline(request.topic, sources, request.content or "")
        elif request.type == "draft":
            prompt = self.prompt_builder.build_draft(request.topic, sources, request.content or "")
        elif request.type == "polished":
            prompt = self.prompt_builder.build_polished(request.topic, sources, request.content or "")
        else:
            prompt = self.prompt_builder.build_title(request.topic, sources, request.content or "")

        # 流式生成 delta 事件
        try:
            for chunk in self.llm_client.generate_stream(prompt):
                yield {"event": "delta", "data": {"text": chunk}}
        except UpstreamError as e:
            logger.error("GenerateStream upstream error: %s", e)
            yield {"event": "error", "data": {"detail": str(e)}}
            return

        # yield done 事件
        logger.info("GenerateStream completed")
        yield {"event": "done", "data": {}}
