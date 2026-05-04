from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str


class Source(BaseModel):
    text: str
    material_id: str | None = None
    score: float | None = None


class GenerateResponse(BaseModel):
    generated_text: str
    sources: list[Source]
