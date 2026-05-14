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
    for event in iterator:
        yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"


@router.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    logger.info("Generate request: topic=%s, type=%s, material_ids=%s", request.topic[:50], request.type, request.material_ids)
    container = get_container()
    response = container.generator.generate(request)
    logger.info("Generate completed: text_length=%d", len(response.generated_text))
    return response


@router.post("/generate/stream")
def generate_stream(request: GenerateRequest) -> StreamingResponse:
    logger.info("Generate stream request: topic=%s, type=%s, material_ids=%s", request.topic[:50], request.type, request.material_ids)
    container = get_container()
    iterator = container.generator.generate_stream(request)
    return StreamingResponse(_sse_stream(iterator), media_type="text/event-stream")
