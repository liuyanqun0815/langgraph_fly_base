import re
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


@patch("app.main.shutdown_chain")
@patch("app.main.startup_chain")
def test_chat_post_without_csrf_returns_403(mock_startup_chain, mock_shutdown_chain):
    with TestClient(app) as client:
        response = client.post("/api/chat", data={"chat": "hello", "sessionId": "abc"})
    assert response.status_code == 403


@patch("app.main.shutdown_chain")
@patch("app.main.startup_chain")
def test_chat_post_with_csrf_returns_200(mock_startup_chain, mock_shutdown_chain):
    with TestClient(app) as client:
        get_resp = client.get("/api/chat")
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_resp.text)
        assert match, "csrf token not in form"
        token = match.group(1)

        with patch("app.routers.chat.flow_control", return_value=[]):
            response = client.post(
                "/api/chat",
                data={"chat": "hello", "sessionId": "abc", "csrfmiddlewaretoken": token},
            )
    assert response.status_code == 200
