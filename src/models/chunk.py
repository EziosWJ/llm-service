from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceChunk:
    text: str
    material_id: str | None = None
    score: float | None = None
