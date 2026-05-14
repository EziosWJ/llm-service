from __future__ import annotations

import json
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.main import app


SSE_EVENTS = [
    {"event": "sources", "data": [{"text": "chunk1", "material_id": "m1", "chunk_index": 0, "score": 0.9}]},
    {"event": "delta", "data": {"text": "hello"}},
    {"event": "delta", "data": {"text": " world"}},
    {"event": "done", "data": {}},
]


def _make_container(events=None):
    container = MagicMock()
    container.generator.generate_stream.return_value = iter(events or SSE_EVENTS)
    return container


def _parse_sse(text: str) -> list[dict[str, str]]:
    """解析 SSE 响应文本，返回 [{event, data}, ...] 列表。"""
    events = []
    current_event = None
    for line in text.splitlines():
        if line.startswith("event: "):
            current_event = line[len("event: "):]
        elif line.startswith("data: ") and current_event is not None:
            events.append({"event": current_event, "data": line[len("data: "):]})
            current_event = None
    return events


def test_generate_stream_returns_sse_events(monkeypatch) -> None:
    """正常流式返回：验证 SSE 事件顺序为 sources -> delta -> done。"""
    container = _make_container()
    monkeypatch.setattr("src.api.generate.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post(
        "/generate/stream",
        json={"type": "draft", "topic": "Topic", "user_id": "u1"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(response.text)
    assert len(events) == 4

    # sources 事件
    assert events[0]["event"] == "sources"
    sources_data = json.loads(events[0]["data"])
    assert len(sources_data) == 1
    assert sources_data[0]["text"] == "chunk1"
    assert sources_data[0]["material_id"] == "m1"
    assert sources_data[0]["chunk_index"] == 0

    # delta 事件
    assert events[1]["event"] == "delta"
    assert json.loads(events[1]["data"]) == {"text": "hello"}

    assert events[2]["event"] == "delta"
    assert json.loads(events[2]["data"]) == {"text": " world"}

    # done 事件
    assert events[3]["event"] == "done"
    assert json.loads(events[3]["data"]) == {}


def test_generate_stream_upstream_error(monkeypatch) -> None:
    """LLM 上游错误时返回 error 事件。"""
    error_events = [
        {"event": "sources", "data": [{"text": "chunk1", "material_id": "m1", "chunk_index": 0, "score": 0.9}]},
        {"event": "error", "data": {"detail": "LLM service unavailable"}},
    ]
    container = _make_container(events=error_events)
    monkeypatch.setattr("src.api.generate.get_container", lambda: container)
    monkeypatch.setattr("src.main.get_container", lambda: container)

    client = TestClient(app)
    response = client.post(
        "/generate/stream",
        json={"type": "draft", "topic": "Topic", "user_id": "u1"},
    )

    assert response.status_code == 200

    events = _parse_sse(response.text)
    assert len(events) == 2
    assert events[0]["event"] == "sources"
    assert events[1]["event"] == "error"
    assert json.loads(events[1]["data"]) == {"detail": "LLM service unavailable"}
