"""响应体 Pydantic 模型，用于 API 出参序列化。"""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """统一错误响应。"""
    error: str
    detail: str


class Source(BaseModel):
    """检索来源片段，附带素材归属与相似度评分。"""
    text: str
    material_id: str | None = None
    chunk_index: int | None = None
    score: float | None = None


class MaterialProcessResponse(BaseModel):
    """素材上传处理响应：deleted_count 为旧向量清理数，chunk_count 为新切片数。"""
    deleted_count: int
    chunk_count: int


class DeleteVectorsResponse(BaseModel):
    """删除向量响应。"""
    deleted_count: int


class GenerateResponse(BaseModel):
    """内容生成响应：generated_text 为生成文本，sources 为 RAG 引用来源。"""
    generated_text: str
    sources: list[Source]


class AskResponse(BaseModel):
    """素材问答响应：answer 为回答文本，sources 为引用来源。"""
    answer: str
    sources: list[Source]
