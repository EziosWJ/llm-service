# 内容生成接口：根据主题和素材生成教学内容，支持同步和 SSE 流式响应

from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from src.bootstrap import get_container
from src.models.requests import GenerateRequest
from src.models.responses import GenerateResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["generate"])


def _sse_stream(iterator):
    """将事件迭代器转为 SSE 格式的文本流（event + data）"""
    for event in iterator:
        yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"


@router.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    """同步生成：根据主题和类型生成教学内容，一次性返回"""
    logger.info("Generate request: topic=%s, type=%s, material_ids=%s", request.topic[:50], request.type, request.material_ids)
    container = get_container()
    response = container.generator.generate(request)
    logger.info("Generate completed: text_length=%d", len(response.generated_text))
    return response


@router.post("/generate/stream")
def generate_stream(request: GenerateRequest) -> StreamingResponse:
    """流式生成：以 SSE 逐步推送生成内容"""
    logger.info("Generate stream request: topic=%s, type=%s, material_ids=%s", request.topic[:50], request.type, request.material_ids)
    container = get_container()
    iterator = container.generator.generate_stream(request)
    return StreamingResponse(_sse_stream(iterator), media_type="text/event-stream")
