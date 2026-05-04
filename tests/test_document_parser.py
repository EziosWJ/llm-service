from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from src.services.document_parser import parse_document


def test_parse_txt_utf8(tmp_path: Path) -> None:
    p = tmp_path / "sample.txt"
    p.write_text("你好\nworld", encoding="utf-8")

    result = parse_document(p)

    assert result["text"] == "你好\nworld"
    assert result["sections"] == []


def test_parse_txt_gbk_fallback(tmp_path: Path) -> None:
    p = tmp_path / "sample.txt"
    p.write_bytes("中文".encode("gbk"))

    result = parse_document(p)

    assert result["text"] == "中文"
    assert result["sections"] == []


def test_parse_txt_latin1_fallback(tmp_path: Path) -> None:
    p = tmp_path / "sample.txt"
    p.write_bytes("café".encode("latin-1"))

    result = parse_document(p)

    assert result["text"] == "café"
    assert result["sections"] == []


def test_parse_docx_heading_123(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_docx = ModuleType("docx")
    fake_doc = SimpleNamespace(
        paragraphs=[
            SimpleNamespace(text="Title", style=SimpleNamespace(name="Heading 1")),
            SimpleNamespace(text="Sub", style=SimpleNamespace(name="Heading 2")),
            SimpleNamespace(text="SubSub", style=SimpleNamespace(name="Heading 3")),
            SimpleNamespace(text="Body", style=SimpleNamespace(name="Normal")),
        ]
    )
    fake_docx.Document = lambda _: fake_doc
    monkeypatch.setitem(sys.modules, "docx", fake_docx)

    p = tmp_path / "sample.docx"
    p.write_bytes(b"stub")
    result = parse_document(p)

    assert result["text"] == "Title\nSub\nSubSub\nBody"
    assert result["sections"] == [
        {"heading": "Title", "level": 1, "content": ""},
        {"heading": "Sub", "level": 2, "content": ""},
        {"heading": "SubSub", "level": 3, "content": ""},
    ]


def test_parse_pdf(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_pypdf = ModuleType("pypdf")
    fake_pypdf.PdfReader = lambda _: SimpleNamespace(
        pages=[
            SimpleNamespace(extract_text=lambda: "Page1"),
            SimpleNamespace(extract_text=lambda: "Page2"),
        ]
    )
    monkeypatch.setitem(sys.modules, "pypdf", fake_pypdf)

    p = tmp_path / "sample.pdf"
    p.write_bytes(b"stub")
    result = parse_document(p)

    assert result["text"] == "Page1\nPage2"
    assert result["sections"] == []


def test_unsupported_type(tmp_path: Path) -> None:
    p = tmp_path / "sample.md"
    p.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_document(p)
