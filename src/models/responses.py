from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str


class Source(BaseModel):
    text: str
    material_id: str | None = None
    chunk_index: int | None = None
    score: float | None = None


class MaterialProcessResponse(BaseModel):
    deleted_count: int
    chunk_count: int


class DeleteVectorsResponse(BaseModel):
    deleted_count: int


class GenerateResponse(BaseModel):
    generated_text: str
    sources: list[Source]


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
