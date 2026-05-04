import re
from typing import Any

from src.models.chunk import Chunk


def _tokenize(text: str) -> list[str]:
    return text.split()


def _detokenize(tokens: list[str]) -> str:
    return " ".join(tokens)


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def _split_long_tokens(tokens: list[str], chunk_size: int, overlap: int) -> list[list[str]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")

    result: list[list[str]] = []
    start = 0
    step = chunk_size - overlap

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        result.append(tokens[start:end])
        if end >= len(tokens):
            break
        start += step
    return result


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
    metadata: dict[str, Any] | None = None,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")

    base_meta = dict(metadata or {})
    chunks: list[Chunk] = []
    paragraphs = _split_paragraphs(text)

    for p_idx, para in enumerate(paragraphs):
        tokens = _tokenize(para)
        if not tokens:
            continue

        if len(tokens) <= chunk_size:
            meta = dict(base_meta)
            meta.update({"paragraph_index": p_idx, "subchunk_index": 0, "token_count": len(tokens)})
            chunks.append(Chunk(text=para, metadata=meta))
            continue

        subchunks = _split_long_tokens(tokens, chunk_size=chunk_size, overlap=overlap)
        for s_idx, sub_tokens in enumerate(subchunks):
            meta = dict(base_meta)
            meta.update(
                {"paragraph_index": p_idx, "subchunk_index": s_idx, "token_count": len(sub_tokens)}
            )
            chunks.append(Chunk(text=_detokenize(sub_tokens), metadata=meta))
    return chunks
