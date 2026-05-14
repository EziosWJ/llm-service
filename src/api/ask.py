from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from src.bootstrap import get_container
from src.models.requests import AskRequest
from src.models.responses import AskResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ask"])


def _sse_stream(iterator):
    for event in iterator:
        yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    logger.info("Ask request: query=%s, material_ids=%s", request.query[:50], request.material_ids)
    container = get_container()
    response = container.ask_service.ask(
        query=request.query,
        material_ids=request.material_ids,
        user_id=request.user_id,
        top_k=request.top_k,
    )
    logger.info("Ask completed: answer_length=%d, sources=%d", len(response.answer), len(response.sources))
    return response


@router.post("/ask/stream")
def ask_stream(request: AskRequest) -> StreamingResponse:
    logger.info("Ask stream request: query=%s, material_ids=%s", request.query[:50], request.material_ids)
    container = get_container()
    iterator = container.ask_service.ask_stream(
        query=request.query,
        material_ids=request.material_ids,
        user_id=request.user_id,
        top_k=request.top_k,
    )
    return StreamingResponse(_sse_stream(iterator), media_type="text/event-stream")
