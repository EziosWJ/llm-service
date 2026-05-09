from __future__ import annotations

import logging

from fastapi import APIRouter

from src.bootstrap import get_container
from src.models.requests import GenerateRequest
from src.models.responses import GenerateResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    logger.info("Generate request: topic=%s, type=%s, material_ids=%s", request.topic[:50], request.type, request.material_ids)
    container = get_container()
    response = container.generator.generate(request)
    logger.info("Generate completed: text_length=%d", len(response.generated_text))
    return response
