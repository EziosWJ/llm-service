from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ParsedSection:
    heading: str
    level: int
    content: str


def parse_document(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext in (".txt", ".md"):
        return _parse_txt(path)
    if ext == ".docx":
        return _parse_docx(path)
    if ext == ".pdf":
        return _parse_pdf(path)
    raise ValueError(f"Unsupported file type: {ext or '<none>'}")


def _parse_txt(path: Path) -> dict[str, Any]:
    last_err: UnicodeDecodeError | None = None
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            text = path.read_text(encoding=enc)
            return {"text": text, "sections": []}
        except UnicodeDecodeError as err:
            last_err = err
    if last_err:
        raise last_err
    return {"text": "", "sections": []}


def _parse_docx(path: Path) -> dict[str, Any]:
    try:
        import docx
    except ImportError as exc:
        raise RuntimeError("python-docx is required for .docx parsing") from exc

    document = docx.Document(str(path))
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
    full_text = "\n".join(paragraphs)

    sections: list[dict[str, Any]] = []
    for p in document.paragraphs:
        raw_text = p.text or ""
        text = raw_text.strip()
        if not text:
            continue
        style_name = getattr(getattr(p, "style", None), "name", "") or ""
        level = _extract_heading_level(style_name)
        if level is not None:
            sections.append({"heading": text, "level": level, "content": ""})

    return {"text": full_text, "sections": sections}


def _extract_heading_level(style_name: str) -> int | None:
    lower = style_name.lower().replace(" ", "")
    if lower == "heading1":
        return 1
    if lower == "heading2":
        return 2
    if lower == "heading3":
        return 3
    return None


def _parse_pdf(path: Path) -> dict[str, Any]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for .pdf parsing") from exc

    reader = PdfReader(str(path))
    texts: list[str] = []
    for page in reader.pages:
        content = page.extract_text() or ""
        if content.strip():
            texts.append(content.strip())
    return {"text": "\n".join(texts), "sections": []}
