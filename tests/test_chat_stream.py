import json
import re
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


async def _fake_stream(question, session_id):
    yield {"type": "progress", "current": 0, "total": 3, "label": "准备执行…"}
    yield {"type": "step_start", "step": 1, "node": "前置安全校验", "input": question}
    yield {"type": "step_end", "step": 1, "node": "前置安全校验", "output": "通过", "status": "ok"}
    yield {"type": "token", "text": "贷款"}
    yield {"type": "token", "text": "用途"}


@patch("app.main.shutdown_chain")
@patch("app.main.startup_chain")
def test_chat_stream_without_csrf_returns_403(mock_startup_chain, mock_shutdown_chain):
    with TestClient(app) as client:
        response = client.post("/api/chat/stream", data={"chat": "hello", "sessionId": "abc"})
    assert response.status_code == 403


@patch("app.main.shutdown_chain")
@patch("app.main.startup_chain")
def test_chat_stream_with_csrf_returns_sse_tokens(mock_startup_chain, mock_shutdown_chain):
    with TestClient(app) as client:
        get_resp = client.get("/api/chat")
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_resp.text)
        assert match, "csrf token not in form"
        token = match.group(1)

        with patch("app.routers.chat.stream_flow_control", new=_fake_stream):
            response = client.post(
                "/api/chat/stream",
                data={"chat": "hello", "sessionId": "abc", "csrfmiddlewaretoken": token},
            )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    events = []
    for block in response.text.strip().split("\n\n"):
        if block.startswith("data: "):
            events.append(json.loads(block[6:]))

    assert events[0]["type"] == "meta"
    assert events[0]["session_id"] == "abc"
    assert any(e.get("type") == "step_start" for e in events)
    assert any(e.get("type") == "progress" for e in events)
    assert any(e.get("type") == "token" for e in events)
    assert events[-1]["type"] == "done"
