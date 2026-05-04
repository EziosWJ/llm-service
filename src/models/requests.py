from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class GenerateRequest(BaseModel):
    type: Literal["outline", "draft", "polished", "title"]
    topic: str = Field(min_length=1)
    content: str | None = None
    material_ids: list[str] | None = None
    user_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)

    @model_validator(mode="after")
    def validate_polished_content(self) -> "GenerateRequest":
        if self.type == "polished" and not (self.content and self.content.strip()):
            raise ValueError("content is required when type=polished")
        return self
