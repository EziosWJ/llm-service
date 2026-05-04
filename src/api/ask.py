from __future__ import annotations

from fastapi import APIRouter

from src.bootstrap import get_container
from src.models.requests import AskRequest
from src.models.responses import AskResponse

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    container = get_container()
    return container.ask_service.ask(
        query=request.query,
        material_ids=request.material_ids,
        user_id=request.user_id,
        top_k=request.top_k,
    )
