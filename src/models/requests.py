"""请求体 Pydantic 模型，用于 API 入参校验。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class GenerateRequest(BaseModel):
    """内容生成请求。

    type: 生成类型 — outline(大纲)/draft(初稿)/polished(润色)/title(标题)
    material_ids: 可选，指定检索哪些素材作为上下文
    top_k: RAG 检索时返回的最相关片段数
    """
    type: Literal["outline", "draft", "polished", "title"]
    topic: str = Field(min_length=1)
    content: str | None = None
    material_ids: list[str] | None = Field(default=None, min_length=1)
    user_id: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)

    @model_validator(mode="after")
    def validate_polished_content(self) -> "GenerateRequest":
        """润色类型必须提供待润色的 content，否则报错。"""
        if self.type == "polished" and not (self.content and self.content.strip()):
            raise ValueError("content is required when type=polished")
        return self


class AskRequest(BaseModel):
    """素材问答请求：根据 query 在关联素材中检索并回答。"""
    query: str = Field(min_length=1)
    material_ids: list[str] | None = Field(default=None, min_length=1)
    user_id: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)
