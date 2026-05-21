"""文本分块数据模型，用于素材切片与检索结果表示。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """素材切片：包含切片文本及元数据（如 material_id、chunk_index 等）。"""
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceChunk:
    """检索命中结果：在 Chunk 基础上附带相似度评分。"""
    text: str
    material_id: str | None = None
    chunk_index: int | None = None
    score: float | None = None
