"""文本分块器：将长文本按段落拆分，超长段落再按固定字符数切块（带重叠）。"""

import logging
import re
from typing import Any

from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


def _split_paragraphs(text: str) -> list[str]:
    """按连续空行拆分文本为段落列表。"""
    parts = re.split(r"\n\s*\n+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def _split_long_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """将单段超长文本按 chunk_size 切分，相邻块之间有 overlap 个字符的重叠以保持上下文连贯。"""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")

    result: list[str] = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = min(start + chunk_size, len(text))
        result.append(text[start:end])
        if end >= len(text):
            break
        start += step
    return result


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
    metadata: dict[str, Any] | None = None,
) -> list[Chunk]:
    """将文本分块并返回 Chunk 列表。短段落直接作为一个块，超长段落按 chunk_size 再切。"""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")

    base_meta = dict(metadata or {})
    chunks: list[Chunk] = []
    paragraphs = _split_paragraphs(text)

    logger.debug("Chunking: text_length=%d, paragraphs=%d, chunk_size=%d, overlap=%d", len(text), len(paragraphs), chunk_size, overlap)

    for p_idx, para in enumerate(paragraphs):
        if not para:
            continue

        if len(para) <= chunk_size:
            meta = dict(base_meta)
            meta.update({"paragraph_index": p_idx, "subchunk_index": 0})
            chunks.append(Chunk(text=para, metadata=meta))
            continue

        subchunks = _split_long_text(para, chunk_size=chunk_size, overlap=overlap)
        for s_idx, sub_text in enumerate(subchunks):
            meta = dict(base_meta)
            meta.update({"paragraph_index": p_idx, "subchunk_index": s_idx})
            chunks.append(Chunk(text=sub_text, metadata=meta))

    logger.debug("Chunking result: %d chunks", len(chunks))
    return chunks
