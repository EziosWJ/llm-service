from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, StrictUndefined

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Build prompts from Jinja templates."""

    def __init__(self, template_dir: str | Path | None = None) -> None:
        if template_dir is None:
            template_dir = Path(__file__).resolve().parents[1] / "templates"
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def build_outline(self, topic: str, sources: str | Iterable[str], content: str = "") -> str:
        return self._render("outline.j2", topic=topic, sources=sources, content=content)

    def build_draft(self, topic: str, sources: str | Iterable[str], content: str) -> str:
        return self._render("draft.j2", topic=topic, sources=sources, content=content)

    def build_polished(self, topic: str, sources: str | Iterable[str], content: str) -> str:
        return self._render("polished.j2", topic=topic, sources=sources, content=content)

    def build_title(self, topic: str, sources: str | Iterable[str], content: str) -> str:
        return self._render("title.j2", topic=topic, sources=sources, content=content)

    def build_ask(self, query: str, sources: str | Iterable[str]) -> str:
        return self._render("ask.j2", query=query, sources=sources)

    def _render(self, template_name: str, **kwargs: str | Iterable[str]) -> str:
        template = self._env.get_template(template_name)
        if "sources" in kwargs:
            kwargs["sources"] = self._normalize_sources(kwargs["sources"])
        logger.debug("Rendering template: %s", template_name)
        return template.render(**kwargs).strip()

    @staticmethod
    def _normalize_sources(sources: str | Iterable[str]) -> str:
        if isinstance(sources, str):
            return sources
        lines = [str(item).strip() for item in sources if str(item).strip()]
        if not lines:
            return "(无来源)"
        return "\n".join(f"- {line}" for line in lines)
