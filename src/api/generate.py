from __future__ import annotations

from fastapi import APIRouter

from src.bootstrap import get_container
from src.models.requests import GenerateRequest
from src.models.responses import GenerateResponse

router = APIRouter(tags=["generate"])


@router.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    container = get_container()
    return container.generator.generate(request)
