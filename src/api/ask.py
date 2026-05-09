from __future__ import annotations

import logging

from fastapi import APIRouter

from src.bootstrap import get_container
from src.models.requests import AskRequest
from src.models.responses import AskResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ask"])


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
